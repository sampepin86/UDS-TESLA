"""
Created on Apr 26, 2016

@author: jpetrie

@description: Abstract Transport is an abstract class for implementing a transport layer for the uds core.
    Supposedly this can be done for LIN and a virtual transport layer, but that is not yet implemented.
    For implementing a CAN Transport Layer, you must implement the following functions:
        get_node_info
        transmit_frame
        receive_frame
        clear_receive_queue
    These are the functions required by the core CAN transport implementation.

    AbstractTransport includes a decorator that implements threadsafety so you don't have to!
    To use it, decorate each of the overloaded methods, (and include a supercall in your __init__ function!)
"""

# Basic Python
from abc import ABCMeta
from abc import abstractmethod
import threading

# Tesla Python
from uds import TeslaUtilities
import uds.nodes as nodes


def threadsafe_check(original_function):
    """
    Use this decorator on any class instance functions that should not be allowed to run over each other. For example,
    a uds rdbi could run over a wdbi if they are called from separate threads.

    The class instance must have a self.lock (threading.Lock) and a self.threadsafe (boolean)
    """
    def new_function(*args, **kwargs):
        self = args[0]
        if self.threadsafe:
            with self.lock:
                return original_function(*args, **kwargs)
        else:
            return original_function(*args, **kwargs)
    return new_function


class AbstractTransport(object):
    """
    Abstract base class for (at least) CAN transport layers for UDS Core.
    """
    __metaclass__ = ABCMeta

    def __init__(self, logger=None, disable_threadsafety=False):
        """
        Constructor
        :param logger: <Logger> A Logger object to use
        :param disable_threadsafety: <boolean> Disables thread-safety checks, if implemented in transport layer
        """
        self.threadsafe = not disable_threadsafety
        self.lock = threading.Lock()

        if logger is None:
            logger = TeslaUtilities.get_logger()
        self._logger = logger

    ''' Hardware Control '''

    @abstractmethod
    def initialize(self):
        """
        Initialize the transport layer hardware
        :return errCode: <number> the error code. 0 means success
        """
        pass

    ''' Main Functions for UDS Core library '''

    # Not abstract, this will be the same for all the transport layers. Will only change if the nodes module changes
    def get_node_info(self, node_id, state):
        """
        From tpNetHandle.h: "This function fill[s] in the CAN parameter[s] from [the] node table."
        It gets called by xxNetGetHandle()
        :param node_id: <uint16_t nodeNum, see tpNetHandle.h> Node number the core C library is requesting
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> State struct to copy data to
        :return success: <bool> The node was successfully found and info updated
        """

        # The struct to be populated is from tpNetHandle.h:
        # typedef struct
        # {
        # uint8_t handleTaken;      // 0 = handle is available, node ID when taken
        # uint8_t blockSize;        // number of block to send, only for CAN
        # uint8_t STmin;            // Client Separation Time minimum, only for CAN
        # uint8_t busNumber;        // bus number to send out the request
        # uint32_t requestID;       // message ID for request, only for CAN
        # uint32_t responseID;      // message ID for response, only for CAN
        # uint32_t driverTimeout;   // timeout value for hardware driver
        # uint16_t nodeNum;         // node number used for gettting the handle
        # uint8_t remoteAddress;    // use for remote address for CAN, but at node Address in LIN
        # uint8_t forcedSTMin;      // forced STMin delay for slower ECU
        # transpDataRequest_t tpDataRequestPtr;
        # transpDataIndication_t tpDataIndicationPtr;
        # } nodeNetworkState_t;

        try:
            node = nodes.node_id_dict[node_id]  # nodes.node_id_dict is a dict of all Node objects in the nodes module
            state.requestID = int(node.requestID)
            state.responseID = int(node.responseID)
            state.busNumber = int(node.busID)
        except KeyError:
            self._logger.error("get_node_info: Could not find a node with the given ID: {0}".format(node_id))
            state.requestID = 0
            state.responseID = 0
            state.busNumber = 0

        # Default values for the data not being stored in the python data stores. Should these ever change?
        #state.handleTaken       Has already been set
        state.blockSize = 0
        state.STmin = 0
        #state.driverTimeout     We're managing transport layer timeouts outside of C
        #state.nodeNum           Has already been set, should be same as handleTaken?
        state.remoteAddress = 0
        state.forcedSTMin = 0
        # Data request and response pointers already got sent when we linked to the transport layer.
        return True

    @abstractmethod
    def transmit_frame(self, state, transmit_buffer):
        """
        Transmit Frame organizes the transmission of a single frame.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param transmit_buffer: <up to 8 bytes of stuff> the buffer to send
        :return success: <bool> Yay/Aww.
        """
        pass

    @abstractmethod
    def receive_frame(self, state, receive_len):
        """
        Receive Frame handles the reception of a frame from the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param receive_len: <number> the length of data to expect.
        :return success, frame: tuple of (bool, double) the success and data read
        """
        pass

    @abstractmethod
    def clear_receive_queue(self, state):
        """
        Clear Receive Queue attempts to clear the receive queue of the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :return success: <bool> yay/aww
        """
        pass

    ''' Other Functions '''

    def set_read_timeout(self, timeout):
        """
        Set the length of time to wait for a message before timing out.
        :param timeout <int>: desired timeout, in seconds.
        """
        self.receive_timeout_seconds = timeout

    @abstractmethod
    def set_node(self, node):
        """
        Signal the transport layer to start capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        pass

    @abstractmethod
    def clear_node(self, node):
        """
        Signal the transport layer to stop capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        pass

    @abstractmethod
    def wait_for_boot_id(self, node, periodic=False, boot_in_app=False):
        """
        Wait for boot ID reads the transport layer looking for the boot ID of the specified node.
        :param node: <uds.nodes.node.Node> the node to reference
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param boot_in_app: <bool> True if ECU is expected to send the message from App
        :return outData: <list of numbers> bootID output
        """
        pass

    @abstractmethod
    def finish(self):
        """
        If the transport layer creates an additional thread for some reason, this method will end that thread
        :return:
        """
        pass

if __name__ == "__main__":
    print __doc__
    print AbstractTransport.__doc__
