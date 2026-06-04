from udsClient import *

# noinspection PyPep8,PyPep8
def parseUDSReturn(fname, value):
    # returns a string that parses the error

    # When a UDS service API execute properly, the return code will be 0 (UDS_OK, refer to UDS_ERROR enum define in udsServices.h).
    # When the API return a non zero value, this indicate an error condition.
    # If the value of the error code is less than 256 (0x100), this indicate an error in transport layer. In this case, refer to the N_RESULT enum define in caNetTransport.h.
    # If the value of the error code is from 0x100 to 0x1FF, this indicate a negative response from ECU (server). The negative response code is the lower 8 bit of the returned error code. Refer to ISO_14229-1_2006-12 document for error condition.
    # Error code 0x200 indicate receive SID is different from requested SID.
    # Error code 0x300 indicate a mismatch in received sub function value. 
    # Error code 0x301 indicate an invalid parameter is being pass to the API.
    # Error code 0x302 indicate an invalid sud function is being pass to udsReadDTCInformation() function.
    # Error code 0x303 indicate server is already in the requested security access level.
    # Error code 0x304 indicate the transport layer callback function is not setup properly.

    CAN_ERROR_LONG = ("This is the general error value. It shall be issued to the service user when an error has been"
                      "detected by the network layer and no other parameter value can be used to better describe"
                      "the error. It can be issued to the service user on both the sender and receiver side.")
    errormap = {
        # This value means that the service execution has completed successfully; it can be issued to a service user on both the sender and receiver side
        0x0     : ("CAN_OK",
                    "This value means that the service execution has completed successfully; it can be issued to a service user on both the sender and receiver side."),
        # all the As, Bs, FS error correspond to the same error in the UDS spec but is used for debugging purposes to indicate different lines of code.
        0x1     : ("CAN_TIMEOUT_A_01",
                    "This value is issued to the protocol user when the timer N_Ar/N_As has passed its time-out value N_Asmax/N_Armax; it can be issued to service user on both the sender and receiver side."),
        0x2     : ("CAN_TIMEOUT_A_02",
                    "This value is issued to the protocol user when the timer N_Ar/N_As has passed its time-out value N_Asmax/N_Armax; it can be issued to service user on both the sender and receiver side."),
        0x3     : ("CAN_TIMEOUT_A_03",
                    "This value is issued to the protocol user when the timer N_Ar/N_As has passed its time-out value N_Asmax/N_Armax; it can be issued to service user on both the sender and receiver side."),
        0x4     : ("CAN_TIMEOUT_Bs_01",
                    "This value is issued to the service user when the timer N_Bs has passed its time-out value N_Bsmax; it can be issued to the service user on the sender side only."),
        0x5     : ("CAN_TIMEOUT_Bs_02",
                    "This value is issued to the service user when the timer N_Bs has passed its time-out value N_Bsmax; it can be issued to the service user on the sender side only."),
        0x6     : ("CAN_TIMEOUT_Cr",
                    "This value is issued to the service user when the timer N_Cr has passed its time-out value N_Crmax; it can be issued to the service user on the receiver side only."),
        0x7     : ("CAN_WRONG_SN",
                    "This value is issued to the service user upon reception of an unexpected sequence number (PCI.SN) value; it can be issued to the service user on the receiver side only."),
        0x8     : ("CAN_INVALID_FS_01",
                    "This value is issued to the service user when an invalid or unknown FlowStatus value has been received in a flow control (FC) N_PDU; it can be issued to the service user on the sender side only."),
        0x9     : ("CAN_INVALID_FS_02",
                    "This value is issued to the service user when an invalid or unknown FlowStatus value has been received in a flow control (FC) N_PDU; it can be issued to the service user on the sender side only."),
        0xA     : ("CAN_UNEXP_PDU_01",
                    "This value is issued to the service user upon reception of an unexpected protocol data unit; it can be issued to the service user on the receiver side only."),
        0xB     : ("CAN_UNEXP_PDU_02",
                    "This value is issued to the service user upon reception of an unexpected protocol data unit; it can be issued to the service user on the receiver side only."),
        0xC     : ("CAN_UNEXP_PDU_03",
                    "This value is issued to the service user upon reception of an unexpected protocol data unit; it can be issued to the service user on the receiver side only."),
        0xD     : ("CAN_UNEXP_PDU_04",
                    "This value is issued to the service user upon reception of an unexpected protocol data unit; it can be issued to the service user on the receiver side only."),
        0xE     : ("CAN_UNEXP_PDU_05",
                    "This value is issued to the service user upon reception of an unexpected protocol data unit; it can be issued to the service user on the receiver side only."),
        0xF     : ("CAN_WFT_OVRN",
                    "This value is issued to the service user upon reception of flow control WAIT frame that exceeds the maximum counter N_WFTmax."),
        0x10    : ("CAN_BUFFER_OVFLW", CAN_ERROR_LONG),
        0x11    : ("CAN_ERROR_01", CAN_ERROR_LONG),
        0x12    : ("CAN_ERROR_02", CAN_ERROR_LONG),
        0x13    : ("CAN_ERROR_03", CAN_ERROR_LONG),
        0x14    : ("CAN_ERROR_04", CAN_ERROR_LONG),
        0x15    : ("CAN_ERROR_05", CAN_ERROR_LONG),
        0x16    : ("CAN_ERROR_06", CAN_ERROR_LONG),
        0x17    : ("CAN_ERROR_07", CAN_ERROR_LONG),
        0x18    : ("CAN_INVALID_HANDLE", None),
        0x19    : ("CAN_LAST_ERROR", None),
        0x200   : ("receive SID is different from requested SID.", None),
        0x300   : ("a mismatch in received sub function value. ", None),
        0x301   : ("an invalid parameter is being pass to the API.", None),
        0x302   : ("an invalid sud function is being pass to udsReadDTCInformation() function.", None),
        0x303   : ("server is already in the requested security access level.", None),
        0x304   : ("the transport layer callback function is not setup properly.", None),
    }

    if value != 0x0:
        try:
            msg = "ERROR [%s] %s\n" % (fname, errormap[value])
        except:
            # Avoids a key error if an error occurs that isn't in the table!
            if (value & 0xF00) == 0x000:   # The upper byte of the error is 0
                msg = "Transport layer error: : {:#x}. Refer to the N_RESULT enum define in caNetTransport.h.".format(value)
            elif (value & 0xF00) == 0x100:      # The upper byte of the error is 1
                msg = "ECU responded with ERROR: {:#x}. The negative response code is the lower 8 bit of the returned error code. Refer to ISO_14229-1_2006-12 document for error condition.".format(value)
            elif (value & 0xF00) == 0x200:      # The upper byte of the error is 2
                msg = "Receive SID is different from requested SID."
            else:
                msg = "UDS client library error {:#x}.".format(value)
        print msg
    return value


# noinspection PyPep8,PyPep8
def parsePCANReturn(value):
    PCAN_ERROR_OK            = TPCANStatus(0x00000)  # No error 
    PCAN_ERROR_XMTFULL       = TPCANStatus(0x00001)  # Transmit buffer in CAN controller is full
    PCAN_ERROR_OVERRUN       = TPCANStatus(0x00002)  # CAN controller was read too late
    PCAN_ERROR_BUSLIGHT      = TPCANStatus(0x00004)  # Bus error: an error counter reached the 'light' limit
    PCAN_ERROR_BUSHEAVY      = TPCANStatus(0x00008)  # Bus error: an error counter reached the 'heavy' limit
    PCAN_ERROR_BUSWARNING    = TPCANStatus(PCAN_ERROR_BUSHEAVY)  # Bus error: an error counter reached the 'warning' limit
    PCAN_ERROR_BUSPASSIVE    = TPCANStatus(0x40000)  # Bus error: the CAN controller is error passive
    PCAN_ERROR_BUSOFF        = TPCANStatus(0x00010)  # Bus error: the CAN controller is in bus-off state
    PCAN_ERROR_ANYBUSERR     = TPCANStatus(PCAN_ERROR_BUSWARNING | PCAN_ERROR_BUSLIGHT | PCAN_ERROR_BUSHEAVY | PCAN_ERROR_BUSOFF | PCAN_ERROR_BUSPASSIVE) # Mask for all bus errors
    PCAN_ERROR_QRCVEMPTY     = TPCANStatus(0x00020)  # Receive queue is empty
    PCAN_ERROR_QOVERRUN      = TPCANStatus(0x00040)  # Receive queue was read too late
    PCAN_ERROR_QXMTFULL      = TPCANStatus(0x00080)  # Transmit queue is full
    PCAN_ERROR_REGTEST       = TPCANStatus(0x00100)  # Test of the CAN controller hardware registers failed (no hardware found)
    PCAN_ERROR_NODRIVER      = TPCANStatus(0x00200)  # Driver not loaded
    PCAN_ERROR_HWINUSE       = TPCANStatus(0x00400)  # Hardware already in use by a Net
    PCAN_ERROR_NETINUSE      = TPCANStatus(0x00800)  # A Client is already connected to the Net
    PCAN_ERROR_ILLHW         = TPCANStatus(0x01400)  # Hardware handle is invalid
    PCAN_ERROR_ILLNET        = TPCANStatus(0x01800)  # Net handle is invalid
    PCAN_ERROR_ILLCLIENT     = TPCANStatus(0x01C00)  # Client handle is invalid
    PCAN_ERROR_ILLHANDLE     = TPCANStatus(PCAN_ERROR_ILLHW | PCAN_ERROR_ILLNET | PCAN_ERROR_ILLCLIENT)  # Mask for all handle errors
    PCAN_ERROR_RESOURCE      = TPCANStatus(0x02000)  # Resource (FIFO, Client, timeout) cannot be created
    PCAN_ERROR_ILLPARAMTYPE  = TPCANStatus(0x04000)  # Invalid parameter
    PCAN_ERROR_ILLPARAMVAL   = TPCANStatus(0x08000)  # Invalid parameter value
    PCAN_ERROR_UNKNOWN       = TPCANStatus(0x10000)  # Unknown error
    PCAN_ERROR_ILLDATA       = TPCANStatus(0x20000)  # Invalid data, function, or action
    PCAN_ERROR_CAUTION       = TPCANStatus(0x2000000)# An operation was successfully carried out, however, irregularities were registered
    PCAN_ERROR_INITIALIZE    = TPCANStatus(0x4000000)# Channel is not initialized [Value was changed from 0x40000 to 0x4000000]
    PCAN_ERROR_ILLOPERATION  = TPCANStatus(0x8000000)# Invalid operation [Value was changed from 0x80000 to 0x8000000]


def wrap(f):
    def wrapped_func(*args, **kwargs):
        return parseUDSReturn(f.__name__, f(*args, **kwargs))
    return wrapped_func

udsDiagnosticSessionControl = wrap(udsDiagnosticSessionControl)
udsECUReset = wrap(udsECUReset)
udsClearDiagnosticInformation = wrap(udsClearDiagnosticInformation)
udsReadDTCInformation = wrap(udsReadDTCInformation)
udsReadDataByIdentifier = wrap(udsReadDataByIdentifier)
udsReadMemoryByAddress = wrap(udsReadMemoryByAddress)
udsSecurityAccessRequestSeed = wrap(udsSecurityAccessRequestSeed)
udsSecurityAccessSendKey = wrap(udsSecurityAccessSendKey)
udsCommunicationControl = wrap(udsCommunicationControl)
udsWriteDataByIdentifier = wrap(udsWriteDataByIdentifier)
udsInputOutputControlByIdentifier = wrap(udsInputOutputControlByIdentifier)
udsRoutineControl = wrap(udsRoutineControl)
udsRequestDownload = wrap(udsRequestDownload)
udsRequestUpload = wrap(udsRequestUpload)
udsTransferData = wrap(udsTransferData)
udsRequestTransferExit = wrap(udsRequestTransferExit)
udsTesterPresent = wrap(udsTesterPresent)
udsWriteMemoryByAddress = wrap(udsWriteMemoryByAddress)
udsControlDTCSetting = wrap(udsControlDTCSetting)
