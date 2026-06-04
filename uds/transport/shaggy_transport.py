"""
Created on Apr 29, 2016

@author: shawkins, adapted from code by jpetrie

@description: shaggy_transport implements the CAN transport layer for udsCLient SWIG using Shaggy and the VAN.
You might say it's.... a VANSport layer

"""

# Basic Python
import time
import datetime
from collections import deque

# Extended Python

# Tesla Python
from abstract_transport import AbstractTransport, threadsafe_check
from abstract_transport_tracer import AbstractTransportTracer
import uds.constants as constants
import uds.utils as utils
import Shaggy

# Constants
MAX_MSG_LEN = 8
BOOTID_TIMEOUT = 30

class ShaggyTransport(AbstractTransport):
    """
    Implements the CAN Transport layer functions for Shaggy/VAN
    """

    def __init__(self, logger=None, shaggy_instance=None,
                 receive_timeout_seconds=constants.DEFAULT_READ_TIMEOUT_SECONDS,
                 receive_wait_seconds=constants.DEFAULT_READ_WAIT_SECONDS, disable_threadsafety=False):
        """
        :param logger: <Logger> Logger instance to use
        :param shaggy_instance: <Shaggy> provide an existing instance of Shaggy if desired
        :param receive_timeout_seconds: <number> seconds to attempt reading a message until timeout
        :param receive_wait_seconds: <number> seconds to wait between message read attempts

        """
        super(ShaggyTransport, self).__init__(logger, disable_threadsafety)

        if shaggy_instance is None:
            shaggy_instance = Shaggy.Shaggy()

        self.shaggy = shaggy_instance
        self.van = self.shaggy.van()
        self.receive_timeout_seconds = receive_timeout_seconds
        self.receive_wait_seconds = receive_wait_seconds
        self.read_queues = {}

    ''' Hardware Control '''

    @threadsafe_check
    def initialize(self, can_bus_id=Shaggy.MM_BUS_CAN_1, can_baud=Shaggy.MM_CAN_BAUD_500K):
        """
        Initialize the VAN for specified bus number and baud
        :param can_bus_id: <int> the CAN bus to use on the VAN. Shaggy.MM_BUS_CAN_X
        :param can_baud: <int> the baud rate. Shaggy.MM_CAN_BAUD_XX
        :return errCode: <number> Shaggy doesn't return an error code so just returning 0 for success
        """
        self.van.connect()
        self.van.baud(can_bus_id, can_baud)     # In theory the shaggy:error object returned can be evaluated as a bool
        return 0

    ''' Main Functions for UDS Core library '''

    @threadsafe_check
    def transmit_frame(self, state, transmit_buffer):
        """
        Transmit Frame organizes the transmission of a single frame.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param transmit_buffer: <up to 8 bytes of stuff> the buffer to send
        :return success: <bool> Yay/Aww.
        """

        # flip the bytes around
        data = utils.from_pcan_byte_array(utils.double_to_array(transmit_buffer), MAX_MSG_LEN)
        data.reverse()
        data = utils.array_to_double(data)

        try:
            self.van.send(state.busNumber, MAX_MSG_LEN, 0, state.requestID, data)
            return True

        except Exception as e:  # Can't raise any exceptions here because the UDS library only accepts a boolean status
            self._logger.error("Transport: Error in transmit_frame")
            self._logger.error(e.message)
            return False

    @threadsafe_check
    def receive_frame(self, state, receive_len):
        """
        Receive Frame handles the reception of a frame from the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param receive_len: <number> the length of data to expect.
        :return success, frame: tuple of (bool, double) the success and data read
        """

        # Try-except block necessary to handle any python exceptions, UDS C library seg faults on null return
        try:
            if state.responseID in self.read_queues:
                num_queued_msgs = len(self.read_queues[state.responseID])
            else:
                # If for some reason the read queue wasn't found, add it.
                self.read_queues[state.responseID] = deque([])
                num_queued_msgs = 0

            response_data = None

            if num_queued_msgs is 0:
                # Nothing stored in the read queue, so poll the VAN to check if a new message has arrived

                response_poll_query = str(state.busNumber) + ":" + hex(state.responseID)
                response = self.van.poll({"signal": response_poll_query})

                start_time = datetime.datetime.now()
                tdelta = datetime.datetime.now() - start_time

                while not response and tdelta.seconds < self.receive_timeout_seconds:
                    response = self.van.poll({"signal": response_poll_query})
                    time.sleep(self.receive_wait_seconds)
                    tdelta = datetime.datetime.now() - start_time

                if response.keys():
                    response_data = response[response.keys()[0]][0]

                    # If the poll returned multiple CAN messages, stash them in a read queue temporarily
                    if len(response[response.keys()[0]]) > 1:
                        for msg in response[response.keys()[0]][1:]:
                            self.read_queues[state.responseID].append(msg)
            else:
                # Use the first message in the read queue, if there is one
                response_data = self.read_queues[state.responseID].popleft()

            if response_data:
                success = 1
                r = utils.from_pcan_byte_array(utils.double_to_array(int(response_data['value'], 16)), 8)
                r.reverse()
                frame = utils.array_to_double(r)
            else:
                self._logger.error("Transport: Timeout while waiting for UDS response")
                success = 0
                frame = 0x0000000000000000  # whew!

        except Exception as e:
            self._logger.error("Transport: Error in receive_frame")
            self._logger.error(e.message)
            success = 0
            frame = 0x0000000000000000

        return success, frame

    @threadsafe_check
    def clear_receive_queue(self, state):
        """
        Clear Receive Queue attempts to clear the receive queue of the hardware.  Not really used right now.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :return success: <bool> yay/aww
        """

        try:
            # DON'T call self.van.flush() here. That's why CAN ID captures were getting dropped (Flush clears them!)

            # Disable and re-enable capture on the VAN to clear its read queue
            response_poll_query = str(state.busNumber) + ":" + hex(state.responseID)
            self.van.capture(response_poll_query, False)
            self.van.capture(response_poll_query, True)

            # Clear our read queue as well
            if state.responseID in self.read_queues:
                self.read_queues[state.responseID].clear()

            success = True
        except Exception as e:
            self._logger.warning("Transport: Error in clear_receive_queue")
            self._logger.warning(e.message)
            success = False

        return success

    @threadsafe_check
    def set_node(self, node):
        """
        Signal the transport layer to start capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """

        response_poll_query = str(int(node.busID)) + ":" + hex(int(node.responseID))
        self.van.capture(response_poll_query, True)
        self.read_queues[int(node.responseID)] = deque([])

    @threadsafe_check
    def clear_node(self, node):
        """
        Signal the transport layer to stop capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """

        # Tell the VAN to stop capturing the specified node
        response_poll_query = str(int(node.busID)) + ":" + hex(int(node.responseID))
        self.van.capture(response_poll_query, False)

        # Delete the read queue associated with that node
        if int(node.responseID) in self.read_queues:
            del self.read_queues[int(node.responseID)]

    @threadsafe_check
    def wait_for_boot_id(self, node, periodic=False, boot_in_app=False):
        """
        Wait for boot ID reads the CAN hardware looking for the boot ID of the specified node.
        :param node: <uds.nodes.node.Node> the node to reference
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param boot_in_app: <bool> True if ECU is expected to send the message from App
        :return out_data: <list of numbers> bootID output
        """

        boot_poll_query = str(int(node.busID)) + ":" + hex(int(node.bootID))
        self.van.capture(boot_poll_query, True)

        if periodic:
            time.sleep(.2)
        else:
            time.sleep(2)

        response = self.van.poll({"signal": boot_poll_query})

        # TODO: Test/verify that this is how this option should be handled
        if boot_in_app:  # test to see if we get boot IDs in app
            # Ignore first boot message from bootloader, look for a second one which will have come from the app?
            response = self.van.poll({"signal": boot_poll_query})

        start_time = time.time()
        while not response:
            response = self.van.poll({"signal": boot_poll_query})

            if (time.time() - start_time) > BOOTID_TIMEOUT:
                self._logger.warning("No boot ID received in 30 seconds! Timeout.")
                break

        self.van.capture(boot_poll_query, False)

        if response:
            response_data = response[response.keys()[0]][0]
            r = utils.from_pcan_byte_array(utils.double_to_array(int(response_data['value'], 16)), 8)
            r.reverse()
            out_data = utils.array_to_double(r)
        else:
            out_data = None

        return out_data

    def finish(self):
        """
        Close any extra threads that may have been created
        """
        pass


class ShaggyTransportTraced(AbstractTransportTracer, ShaggyTransport, AbstractTransport):
    pass

if __name__ == '__main__':
    print __doc__
    print ShaggyTransport.__doc__
