"""
Created on Jun 7, 2016

@author: trseroff

@description: Wrapper for abstract transport layer which logs the messages received and transmitted
"""
# Basic Python

# Extended Python
# TODO: don't use TPCANMsg (or any part of PCANBasic)
from PCAN.PCANBasic import TPCANMsg
from abc import ABCMeta

# Tesla Python
from abstract_transport import AbstractTransport
from PCAN.PEAKTrace import CANTracer
import uds.utils as utils
from uds import TeslaUtilities


class AbstractTransportTracer(AbstractTransport):
    """
    AbstractTransportTracer is an AbstractTransport class which logs messages and then passes them on.
    """
    __metaclass__ = ABCMeta

    def __init__(self, trace_file, logger, *args):
        """
        Constructor
        :param trace_file: <string> path to desired trace file
        :param logger: logger object to use
        """
        if logger is None:
            logger = TeslaUtilities.get_logger()
        self._logger = logger
        super(AbstractTransportTracer, self).__init__(logger, *args)
        self.can_tracer = CANTracer(trace_file)


    def update_can_trace_filename(self, trace_file):
        """
        Update CAN Trace Filename changes the trace file. Ends the current trace.
        :param trace_file: <string> full path to the new trace file.
        """
        self.can_tracer.abort = True
        self.can_tracer.join()
        self.can_tracer = CANTracer(trace_file)

    ''' Transport layer functions '''

    def transmit_frame(self, state, transmit_buffer):
        """
        Reads parameter data to log it, then passes it through to the transport layer. 
        """
        try:
            message = TPCANMsg()
            message.LEN = 8  # MAX_MSG_LEN
            message.ID = state.requestID
            message.DATA = utils.double_to_array(transmit_buffer)
            self.can_tracer.write_can_message(message)
        except Exception as e:
            self._logger.warning("TransportTracer transmit_frame error: " + e.message)

        return super(AbstractTransportTracer, self).transmit_frame(state, transmit_buffer)

    def receive_frame(self, state, receive_len):
        """
        Reads parameter and return data to log it, then passes it through to the transport layer. 
        """
        success, frame = super(AbstractTransportTracer, self).receive_frame(state, receive_len)

        try:
            message = TPCANMsg()
            message.LEN = receive_len
            message.ID = state.responseID
            message.DATA = utils.double_to_array(frame)
            self.can_tracer.read_can_message(message)
        except Exception as e:
            self._logger.warning("TransportTracer receive_frame error: " + e.message)

        return success, frame

    ''' Threading Functions '''

    def finish(self):
        """
        Ends the CAN tracer thread.
        """
        self.can_tracer.abort = True
        try:
            super(AbstractTransportTracer, self).finish()
        except:
            pass

    def join(self):
        """
        Pass through to the CAN tracer thread.
        """
        self.can_tracer.join()


if __name__ == '__main__':
    print __doc__
    print AbstractTransportTracer.__doc__
