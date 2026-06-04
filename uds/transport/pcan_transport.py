"""
Created on Apr 14, 2016

@author: jpetrie

@description: PCANTransport is a class to implement the CAN Network Transport layer for udsCLient SWIG using PCAN
"""

# Basic Python
import time
import datetime

# Extended Python
import PCAN.PCANBasic as PB

# Tesla Python
from abstract_transport import AbstractTransport, threadsafe_check
from abstract_transport_tracer import AbstractTransportTracer
import queue_thread
import uds.utils as utils
import uds.constants as constants

# Constants
PCAN_SLEEPY = 1
MAX_MSG_LEN = 8
BOOTID_TIMEOUT = 30


class PCANTransport(AbstractTransport):
    """
    Implements the CAN Transport layer functions for PCAN
    """

    def __init__(self, logger=None, bus=PB.PCAN_USBBUS1, baud=PB.PCAN_BAUD_500K, can_hardware=None,
                 receive_timeout_seconds=constants.DEFAULT_READ_TIMEOUT_SECONDS,
                 receive_wait_seconds=constants.DEFAULT_READ_WAIT_SECONDS, disable_threadsafety=False):
        """
        :param logger: A logger object to use
        :param bus: <TPCANHandle> The handle representing the CAN hardware
        :param baud: <TPCANBaudrate> the baudrate to run the hardware
        :param can_hardware: <PCANBasic> an instance of CAN Hardware interface thread
        :param receive_timeout_seconds: <number> seconds to attempt reading a message until timeout
        :param receive_wait_seconds: <number> seconds to wait between message read attempts
        """
        super(PCANTransport, self).__init__(logger, disable_threadsafety)

        if can_hardware is None:
            can_hardware = PB.PCANBasic()
        self.can = can_hardware

        self._bus = bus
        self._baud = baud
        self.receive_timeout_seconds = receive_timeout_seconds
        self.receive_wait_seconds = receive_wait_seconds
        self.transmitting = False

        # Make a read and boot message queue thread, give it a pointer to the read function
        self.queue_thread = queue_thread.QueueThread(self.read_helper)

    ''' Hardware control '''
    @threadsafe_check
    def initialize(self, clear_filters=True):
        """
        Initialize the PCAN hardware
        :return errCode: <number> the error code provided by the PCAN DLL. 0 means success
        """
        err_code = self.can.Initialize(self._bus, self._baud)
        if err_code != 0:
            self._logger.info("Could not initialize PCAN")
            err_code = self._reinitialize()
        else:
            self._logger.info("PCAN Initialized.")
            self.queue_thread.start()

        if clear_filters:
            # If the hardware isn't already in use, we should clear the hardware filters unless told not to.
            self.can.SetValue(self._bus, PB.PCAN_MESSAGE_FILTER, 0)

        return err_code

    # No threadsafe_check here because initialize() won't free the lock before calling reinitialize()
    def _reinitialize(self):
        """
        Reinitialize is a last ditch effort to re initialize the CAN hardware.
        """
        self._logger.info("Reinitializing PCAN...")
        err_code = self.can.Uninitialize(self._bus)
        if err_code == 0:
            time.sleep(PCAN_SLEEPY)
            err_code = self.can.Initialize(self._bus, self._baud)
            if err_code == 0:
                self._logger.info("PCAN Initialized.")
                self.queue_thread.start()
            else:
                msg = "PCAN did not reinitialize! Error Code: 0x{0:x}".format(err_code)
                self._logger.error(msg)
                raise Exception(msg)  # TODO: Use a more interesting Exception
        else:
            msg = "Couldn't uninitialize PCAN! Error Code: 0x{0:x}.".format(err_code)
            self._logger.error(msg)
            raise Exception(msg)  # TODO: Use a more interesting Exception
        return err_code

    @threadsafe_check
    def read_helper(self):
        """
        read_helper - abstracts PCAN API function Read into a no-argument read function that the queue thread can access
        :return: the message received
        """
        while self.transmitting:
            pass
        received_msg = self.can.Read(self._bus)
        res, msg, _ = received_msg  # Discard the timestamp

        if res > 0:
            # Return code isn't 0, so we didn't get a good read
            return None
        else:
            # Got a good message, pass it back to the queue thread.
            return msg

    ''' Main Functions for UDS Core library '''

    @threadsafe_check
    def transmit_frame(self, state, transmit_buffer):
        """
        Transmit Frame organizes the transmission of a single frame.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> The state.
        :param transmit_buffer: <up to 8 bytes of stuff> the buffer to send
        :return success: <bool> Yay/Aww.
        """
        try:
            message = PB.TPCANMsg()
            message.ID = state.requestID
            message.LEN = MAX_MSG_LEN  # Some day we will be able to send less than max.
            message.MSGTYPE = PB.PCAN_MESSAGE_STANDARD  # For now we only live in the 11bit ID world.

            message.DATA = utils.double_to_array(transmit_buffer)

            self.transmitting = True
            return_code = self.can.Write(self._bus, message)
            self.transmitting = False
            success = (return_code == 0)

        except Exception as e:
            self._logger.warning("Transport: Error in transmit_frame")
            self._logger.warning(e.message)
            success = 0

        return success

    @threadsafe_check
    def write(self, message):
        """
        Transmit a custom TPCANMsg message to the PCANBasic instance.
        Necessary for sending messages shorter than 8 bytes
        :param message <TPCANMsg>: the CAN message to send
        :return: <TPCANStatus>: The return code from the PCAN dongle.
        """
        return self.can.Write(self._bus, message)

    # Multiple instances are able to pull from their respective read queues simultaneously
    def receive_frame(self, state, receive_len):
        """
        Receive Frame handles the reception of a frame from the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param receive_len: <number> the length of data to expect.
        :return success, frame: tuple of (bool, double) the success and data read
        """
        try:
            start_time = time.time()
            success = 0
            frame = 0x0000000000000000
            
            orig_timeout = self.queue_thread._timeout
            
            while (time.time() - start_time) < self.receive_timeout_seconds:
                # Use a very short timeout on read to quickly poll/drain any queued frames
                self.queue_thread.set_read_timeout(0.005)
                read_message = self.queue_thread.read(state.responseID)
                
                if read_message:
                    # Validate ISO-TP PCI (Protocol Control Information) byte
                    pci_type = (read_message.DATA[0] >> 4) & 0x0F
                    is_valid = False
                    if pci_type == 0: # Single Frame
                        sf_len = read_message.DATA[0] & 0x0F
                        if 1 <= sf_len <= 7:
                            is_valid = True
                    elif pci_type in (1, 2, 3): # FF, CF, FC
                        is_valid = True
                        
                    if is_valid:
                        success = 1
                        frame = utils.array_to_double(read_message.DATA)
                        break
                    # Invalid ISO-TP: discard periodic status message and check the next one
                else:
                    time.sleep(0.005)
                    
            self.queue_thread.set_read_timeout(orig_timeout)
            
            if not success:
                self._logger.warning("Transport: Timeout while waiting for UDS response")

        except Exception as e:
            self._logger.warning("Transport: Error in receive_frame")
            self._logger.warning(e.message)
            success = 0
            frame = 0x0000000000000000

        return success, frame

    @threadsafe_check
    def clear_receive_queue(self, state):
        """
        Clear Receive Queue attempts to clear the receive queue of the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :return success: <bool> yay/aww
        """
        try:
            success = self.queue_thread.clear_queues(state.requestID)  # Cross your fingers.
        except Exception as e:
            self._logger.warning("Transport: Error in clear_receive_queue")
            self._logger.warning(e.message)
            success = False

        return success

    ''' UDS Helper Functions '''

    @threadsafe_check
    def set_node(self, node):
        """
        Signal the transport layer to start capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        self.queue_thread.add_read_queue(int(node.responseID))
        self.can.FilterMessages(self._bus, int(node.responseID), int(node.responseID), PB.PCAN_MODE_STANDARD)

    @threadsafe_check
    def clear_node(self, node):
        """
        Signal the transport layer to stop capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        self.queue_thread.remove_read_queue(int(node.responseID))

    def wait_for_boot_id(self, node, periodic=False, boot_in_app=False):
        """
        Wait for boot ID reads the CAN hardware looking for the boot ID of the specified node.
        :param node: <uds.nodes.node.Node> the node to reference
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param boot_in_app: <bool> True if ECU is expected to send the message from App
        :return out_data: <list of numbers> bootID output
        """
        boot_id = int(node.bootID)
        self.can.FilterMessages(self._bus, boot_id, boot_id, PB.PCAN_MODE_STANDARD)
        self.queue_thread.add_read_queue(boot_id)

        if periodic:
            time.sleep(constants.DEFAULT_READ_WAIT_SECONDS)
        else:
            time.sleep(2)

        read = self.queue_thread.read(boot_id)

        if boot_in_app:  # test to see if we get boot IDs in app
            read = self.queue_thread.read(boot_id)

        start_time = time.time()
        while read is None:
            read = self.queue_thread.read(boot_id)

            if (time.time() - start_time) > BOOTID_TIMEOUT:
                self._logger.warning("No boot ID received in 30 seconds! Timeout.")
                break

        self.queue_thread.remove_read_queue(boot_id)

        if read:
            out_data = utils.from_pcan_byte_array(read.DATA, read.LEN)
        else:
            out_data = None

        return out_data

    ''' Other Config '''
    def set_read_timeout(self, timeout):
        """
        Set the length of time to wait for a message before timing out.
        :param timeout <int>: desired timeout, in seconds.
        """
        self.receive_timeout_seconds = timeout
        self.queue_thread.set_read_timeout(timeout)

    def finish(self):
        """
        End the QueueThread thread, which has been running to keep the read queues filled
        """
        uninit_count = 0
        try:
            # TODO: is this the right way to uninit?
            while self.can.Uninitialize(self._bus) != PB.PCAN_ERROR_OK:
                time.sleep(.2)  # just to make sure that pcan exits
                uninit_count += 1
                if uninit_count > 3:
                    raise Exception("Cannot un-initialize PCAN!")
        finally:
            self.queue_thread.finish()


class PCANTransportTraced(AbstractTransportTracer, PCANTransport, AbstractTransport):
    pass


if __name__ == '__main__':
    print __doc__
    print PCANTransport.__doc__
