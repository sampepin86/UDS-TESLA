"""
Created on 7/15/16

@author: shawkins

This is a dummy transport layer that responds with a few canned messages, the way an SNSUS might messages.

The commands that are expected to work are enumerated below.
"""

# base python
import random
import time

# Tesla Python
from abstract_transport import AbstractTransport, threadsafe_check
import uds.utils as utils

# states
UNKNOWN_STATE = "UNKNOWN_STATE"
REQUESTING_TP = "REQUESTING_TP"
REQUESTING_RDBI_0x101_3 = "REQUESTING_RDBI"
REQUESTING_WDBI_0xF01C_0 = "REQUESTING_WDBI"
REQUESTING_SA_5 = "REQUESTING_SA"
REQUESTING_RESET_HARD_TRUE = "REQUESTING_RESET"
REQUESTING_SESSION_CHANGE_PROGRAMMING_TRUE = "REQUESTION_SESSION"
REQUESTING_RC_0x1_0x1_NONE_0 = "REQUESTING_RC"
REQUESTING_IOC_0x1_0x1_0_0 = "REQUESTING_IOC"
REQUESTING_SESSION_DEFAULT = "REQUESTING_SESSION_DEFAULT"
REQUESTING_SESSION_EXTENDED = "REQUESTING_SESSION_EXTENDED"
REQUESTING_SA_01_SEED = "REQUESTING_SA_01_SEED"
REQUESTING_RESET_SOFT = "REQUESTING_RESET_SOFT"
REQUESTING_CLEAR_DTC = "REQUESTING_CLEAR_DTC"
REQUESTING_READ_DTC = "REQUESTING_READ_DTC"

# Format: 8-byte double packed as [length | SID | data... | 0x55 padding]
expected_inputs = {
    0x23e005555555555: REQUESTING_TP,
    0x322010155555555: REQUESTING_RDBI_0x101_3,
    0x42ef01c00555555: REQUESTING_WDBI_0xF01C_0,
    0x227055555555555: REQUESTING_SA_5,
    0x211015555555555: REQUESTING_RESET_HARD_TRUE,
    0x210025555555555: REQUESTING_SESSION_CHANGE_PROGRAMMING_TRUE,
    0x431010001555555: REQUESTING_RC_0x1_0x1_NONE_0,
    0x52f000101005555: REQUESTING_IOC_0x1_0x1_0_0,
    # Common GUI requests
    0x210015555555555: REQUESTING_SESSION_DEFAULT,       # 0x10 0x01 (DefaultSession)
    0x210035555555555: REQUESTING_SESSION_EXTENDED,      # 0x10 0x03 (ExtendedDiagnostic)
    0x227015555555555: REQUESTING_SA_01_SEED,            # 0x27 0x01 (SecurityAccess seed)
    0x211025555555555: REQUESTING_RESET_SOFT,            # 0x11 0x02 (SoftReset)
    0x414FFFFFF555555: REQUESTING_CLEAR_DTC,             # 0x14 0xFF 0xFF 0xFF (ClearDTC)
    0x31902FF55555555: REQUESTING_READ_DTC,              # 0x19 0x02 0xFF (ReadDTCByStatusMask)
}

canned_responses = {
    REQUESTING_TP:                              0x027E00AAAAAAAAAA,
    REQUESTING_RDBI_0x101_3:                   0x06620101000005AA,
    REQUESTING_WDBI_0xF01C_0:                  0x036EF01C00000000,
    REQUESTING_SA_5:                           0x026706AAAAAAAAAA,
    REQUESTING_RESET_HARD_TRUE:                0x025101AAAAAAAAAA,
    REQUESTING_SESSION_CHANGE_PROGRAMMING_TRUE: 0x065002001400C8AA,
    REQUESTING_RC_0x1_0x1_NONE_0:             0x065002001400C8AA,
    # Positive responses for common GUI services
    REQUESTING_SESSION_DEFAULT:    0x065001001400C8AA,  # DefaultSession OK (P2=20ms, P2*=5000ms)
    REQUESTING_SESSION_EXTENDED:   0x065003001400C8AA,  # ExtendedDiagnostic OK
    REQUESTING_SA_01_SEED:         0x046701DEADBEEFAA,  # SecurityAccess seed = 0xDEADBEEF
    REQUESTING_RESET_SOFT:         0x025102AAAAAAAAAA,  # SoftReset OK
    REQUESTING_CLEAR_DTC:          0x015400AAAAAAAAAA,  # ClearDTC OK
    REQUESTING_READ_DTC:           0x025902AAAAAAAAAA,  # ReadDTC: 0 DTCs found
}


class SimulatedTransport(AbstractTransport):
    """
    Has some canned responses, simulating data coming back across some hardware.

    Optionally adds an artificial delay to "simulate" hardware and test thread safety
    """

    def __init__(self, logger=None, verbose=True, random_sleep_max_duration=0.5, disable_threadsafety=False):
        """
        :param verbose: print or shut up
        :type verbose: bool
        :param random_sleep_max_duration: max time to (randomly) sleep during transmit to simulate hardware speed
        :type random_sleep_max_duration: float or bool
        :param disable_threadsafety: don't turn this off, k? it's not what you want, promise. (but it does what it says)
        :type disable_threadsafety: bool
        """
        super(SimulatedTransport, self).__init__(logger, disable_threadsafety)
        self._logger = logger
        self.state = UNKNOWN_STATE
        self.verbose = verbose
        self.random_sleep_max_duration = random_sleep_max_duration

    # Hardware Control

    @threadsafe_check
    def initialize(self):
        return 0

    # Main Functions for UDS Core library

    @threadsafe_check
    def transmit_frame(self, state, transmit_buffer):
        """
        Transmit Frame organizes the transmission of a single frame.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param transmit_buffer: <up to 8 bytes of stuff> the buffer to send
        :return success: <bool> Yay/Aww.
        """
        if self.verbose:
            print "transmitting:", hex(transmit_buffer)
        # DEBUG: always print exact value for key matching verification
        print "[SIM_DBG] TX frame: 0x{:016X}  match={}".format(
            transmit_buffer, transmit_buffer in expected_inputs)
        if transmit_buffer in expected_inputs.keys():
            self.state = expected_inputs[transmit_buffer]
            if self.verbose:
                print "State change", self.state
        else:
            self.state = "DYNAMIC"
            self.last_tx = transmit_buffer
        return True

    @threadsafe_check
    def receive_frame(self, state, receive_len):
        """
        Receive Frame handles the reception of a frame from the hardware.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :param receive_len: <number> the length of data to expect.
        :return success, frame: tuple of (bool, double) the success and data read
        """
        if self.random_sleep_max_duration:
            sleep_duration = random.randint(0, int(10 * self.random_sleep_max_duration)) / 10.0
            if self.verbose:
                print "sleeping for", sleep_duration, "seconds"
            time.sleep(sleep_duration)
            
        response = 0x0
        if self.state in canned_responses.keys():
            if self.verbose:
                print "found canned response, 'receiving:' ", hex(canned_responses[self.state])
            response = canned_responses[self.state]
        elif self.state == "DYNAMIC":
            tx = self.last_tx
            sid = (tx >> 48) & 0xFF
            sub = (tx >> 40) & 0xFF
            resp_sid = sid + 0x40

            # Map SID -> expected positive response payload length
            # (response length = 1 byte resp_sid + payload)
            service_resp_len = {
                0x10: 6,  # DSC: resp_sid + sessionType + P2(2) + P2*(2)
                0x11: 2,  # ECUReset: resp_sid + resetType
                0x14: 1,  # ClearDTC: just resp_sid
                0x19: 2,  # ReadDTC: resp_sid + statusAvail
                0x22: 4,  # ReadDBI: resp_sid + DID(2) + data(1 min)
                0x27: 6,  # SecurityAccess: resp_sid + level + seed(4)
                0x28: 2,  # CommunicationControl: resp_sid + controlType
                0x2E: 3,  # WriteDBI: resp_sid + DID(2)
                0x2F: 4,  # IOControl: resp_sid + DID(2) + controlParam
                0x31: 4,  # RoutineControl: resp_sid + type + id(2)
                0x3E: 2,  # TesterPresent: resp_sid + subFunction
                0x85: 2,  # ControlDTCSetting: resp_sid + settingType
            }
            resp_len = service_resp_len.get(sid, 2)

            # Build response: [resp_len | resp_sid | sub | 0xAA padding...]
            response = (resp_len << 56) | (resp_sid << 48) | (sub << 40) | 0x0000AAAAAAAAAAAA

            if self.verbose:
                print "generated dynamic response (SID 0x{:02X}, len {}): 0x{:016X}".format(sid, resp_len, response)
                
        return 1, response

    @threadsafe_check
    def clear_receive_queue(self, state):
        """
        Clear Receive Queue attempts to clear the receive queue of the hardware.  Not really used right now.
        :param state: <nodeNetworkState_t, see tpNetHandle.h in UDS core client source> the state.
        :return success: <bool> yay/aww
        """
        self.state = UNKNOWN_STATE
        return True

    def set_node(self, node):
        """
        Signal the transport layer to start capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        pass

    def clear_node(self, node):
        """
        Signal the transport layer to stop capturing messages for the specified node
        :param node: <uds.nodes.node.Node> the node to reference
        """
        pass

    @threadsafe_check
    def wait_for_boot_id(self, node=None, periodic=False, boot_in_app=False):
        """
        Wait for boot ID reads the transport layer looking for a boot ID. Uses specified node if none given.
        :param node: <uds.nodes.node.Node> the node to reference
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param boot_in_app: <bool> True if ECU is expected to send the message from App
        :return out_data: <list of numbers> bootID output
        """
        out_data = utils.array_to_double([0xd, 0xe, 0xa, 0xd, 0xd, 0xe, 0xa, 0xd])
        return out_data

    def finish(self):
        """
        Close any extra threads that may have been created
        :return:
        """
        pass


if __name__ == '__main__':
    print __doc__
    print SimulatedTransport.__doc__
