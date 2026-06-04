"""
Author: Ellinor Crux (elcrux@tesla.com)

About: Implmentation of the Abstract Transport to work with the CP tester team's DUTAL interface

"""
# import time
# import utils  # UDS.utils
#
# from transport import abstract_transport
# # from DUTAL import DUTAL

import time
import traceback
import uds.utils as utils
from abstract_transport import AbstractTransport
from abstract_transport_tracer import AbstractTransportTracer


class msg(object):
    def __init__(self, ID, length, data):
        self.id = ID
        self.length = length
        self.data = data

class DUTAL_transport(AbstractTransport):
    """
    Implements the Abstract Transport layer for DUTAL (Device Under Test Abstraction Layer)
    """

    def __init__(self, logger=None, hw_reference=None,
                 receive_timeout_seconds=None,
                 receive_wait_seconds=None, disable_threadsafety=False):

        """
        Constructor
        :param hw_reference: existing DUTAL instance to be used
        :param receive_timeout_seconds: <number> seconds to attempt reading a message until timeout
        :param receive_wait_seconds: <number> seconds to wait between message read attempts
        """
        super(DUTAL_transport, self).__init__(logger, disable_threadsafety)

        if hw_reference is not None:
            self._dutal_instance = hw_reference
            self.single_use = False  # Don't kill dutal when done with UDS.
        # else:
        #     self._dutal_instance = DUTAL(threadID, name, logger, DBC, AcyclicFlag, AcyclicMsg, TXCANDict, AlertDict, TXCANSignal, RXCANSignal)
        #     self.single_use = True  # This means that it will kill the DUTAL thread it created once it's done
        #  TODO: For now, this thing will only work if you pass it a dutal instance.
        if not receive_timeout_seconds:
            self.receive_timeout = 15
        else:
            self.receive_timeout = receive_timeout_seconds
        if not receive_wait_seconds:
            self.receive_wait_seconds = .01
        else:
            self.receive_wait_seconds = receive_wait_seconds
        self._logger = logger
        self._boot_id = 0x000

    def initialize(self):
        """
        Initialize the transport layer hardware
        :return errCode: <number> the error code. 0 means success
        """
        # if self._dutal_instance.isAlive():
        #     pass
        # else:
        #     self._dutal_instance.run()

        return 0

    ''' Main Functions for UDS Core library '''

    def transmit_frame(self, state, transmit_buffer):
        """
        Transmit Frame organizes the transmission of a single frame.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param transmit_buffer: <up to 8 bytes of stuff> the buffer to send
        :return success: <bool> Yay/Aww.
        """
        msg_id = state.requestID
        msg_len = 8  # TODO: Maximum length. Maybe it would be nice to read the length...
        msg_data = []

        # Format the data correctly:
        data = utils.double_to_array(transmit_buffer)
        for i in xrange(0, len(data)):
            msg_data.append(data[i])

        # Send it:
        status_code = self._dutal_instance.write_raw_can_frame(msg_id, msg_len, msg_data)

        return status_code == 0

    def receive_frame(self, state, receive_len):
        """
        Receive Frame handles the reception of a frame from the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param receive_len: <number> the length of data to expect.
        :return success, frame: tuple of (bool, double) the success and data read
        """
        success = False

        try:

            msg_id = state.responseID  # This is the message we want to listen for
            frame = 0

            #  Read the messages:

            success, content = self._read_helper(msg_id, self.receive_wait_seconds, self.receive_timeout)

            if success:  # If we're able to read, process the message into the right format

                # There's a lot of complicated stuff going on here, so let me summarize it:
                # Data comes in as an int
                # When you cast that data to hex, it is big endian overall, but small endian within bytes
                # First we make it into a hex string, remove unnecessary stuff, like the "L" and "0x"
                # Then I pad it with the trailing zeros at the front
                # Then I make a string beginning in "0x" where I can make the hex data small endian overall (hex_data)
                # Then we go through "data", taking each byte from the end and appending it to hex_data
                # And cast it back into a decimal number to pass to UDSpy
                # for example, 0x563412 would become 0x1234560000000000 and then cast to a decimal number

                data = str(hex(content[2]))  # Make it into a hex string
                self._logger.debug("Incoming raw message data from DUTAL:  " + data)
                data = data[2:len(data)]  # get rid of the "0x"

                if data[len(data)-1] == "L":
                    data = data[0:len(data)-1]  # Get rid of the "L" at the end

                data = data.zfill(16)  # Add in the zeros that are missing at the front (trailing zeros)

                num_of_hex_entries = len(data)/2  # This is how many bytes should be in the hex_data list

                spot = len(data)  # This is the beginning of the last byte in "data"
                hex_data = "0x"  # Make a spot to put the processed hex data

                # Put the hex data into the right order (make it small endian overall):

                for i in xrange(0, num_of_hex_entries):

                    hex_data += data[spot-2:spot]  # Grab the byte at the very end and append it to hex_data
                    spot -= 2  # Go backwards one byte (2 characters)

                self._logger.debug("Incoming message data was processed as: " + hex_data)

                # Cast it back to a decimal number:
                frame = int(hex_data, 16)

        except:
            self._logger.error("An uncaught exception occurred while trying to read & process messages from DUTAL")
            traceback.print_exc()

        return success, frame

    def clear_receive_queue(self, state):
        """
        Clear Receive Queue attempts to clear the receive queue of the hardware.  Not really used right now.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :return success: <bool> yay/aww
        Not useful for DUTAL
        """
        return True

    ''' Other Functions '''

    def set_node(self, node):
        """
        Signal the transport layer to start capturing messages for the specified node
        :param node: <UDS.Nodes.Node> the node to reference
        """
        pass

    def clear_node(self, node):
        """
        Signal the transport layer to stop capturing messages for the specified node
        :param node: <UDS.Nodes.Node> the node to reference
        """
        pass

    def wait_for_boot_id(self, node, periodic=False, boot_in_app=False):
        """
        Wait for boot ID reads the CAN hardware looking for the boot ID of the specified node.
        :param node: <UDS.Nodes.Node> the node to reference
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param boot_in_app: <bool> True if ECU is expected to send the message from App
        :return out_data: <list of numbers> bootID output
        """

        msg_id = int(node.bootID)

        success, content = self._read_helper(msg_id, 0.1, 30)

        if not success:
            self._logger.warning("Transport: Timeout while waiting for boot id")

        out_data = content[2]

        return out_data

    def finish(self):
        """
        If the transport layer creates an additional thread for some reason, this method will end that thread
        :return:
        """
        if self.single_use:
            self._dutal_instance.join()
            # If we're only using DUTAL for UDS, then it should kill it when it's done. Otherwise leave it alone.
        else:
            pass

    def _read_helper(self, msg_id, wait_time, timeout):
        """
        Looks for a specific message until it finds it or times out
        :param msg_id: the hex value for the message you want
        :param wait_time: how long in between readings (seconds)
        :param timeout: how long before you stop looking (seconds)
        :return: success, content
        content is a touple with (msg_id, msg_len, msg_data), note msg_data is an int
        """

        start_time = time.time()
        elapsed_time = 0
        success = False
        content = (0, 0, 0)  # TODO: Is this the right thing here?
        try:
            while elapsed_time < timeout:
                content = self._dutal_instance.read_raw_can_frame()
                try:
                    if content[0] == msg_id:
                        success = True
                        break
                except TypeError:  # There was no message to read
                    pass
                time.sleep(wait_time)
                elapsed_time = time.time() - start_time
        except:
            self._logger.error("Transport: An uncaught exception occurred while trying to read raw CAN messages")
            traceback.print_exc()

        if elapsed_time > timeout:
            self._logger.warning("Transport: Timeout while reading messages")

        return success, content


class DUTALTransportTraced(AbstractTransportTracer, DUTAL_transport, AbstractTransport):
    pass

if __name__ == "__main__":
    print __doc__
    print DUTAL_transport.__doc__
