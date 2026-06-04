"""
Created on Apr 14, 2016

@author: jpetrie

@description: Client is an interface class for udsClient swig python.

"""

# Base Python
import threading

# Extended Python
from uds.hexLib import Hex, Hex16bit  # TODO: Figure out if the real intelHex (from pypi) will work instead.

# Tesla Python
import utils
import nodes
import TeslaUtilities
import core.udsClientWrapped as udsCore
from transport.abstract_transport import threadsafe_check
from uds.typedefs import UdsModuleID

# Constants
MAX_SEED_SIZE = 20  # Number of bytes expected from the server after requesting a security seed. Max key/seed size.
KEYGEN_MASK = 53  # Used to transform seed into valid key for security access. TODO: Convince Tesla to be more creative.
DL_CHUNK_SIZE = 0x3F0  # Size of data chunk to be sent in each data transfer cycle.
#                        A data transfer cycle is: request_download_init, request_transfer, request_transfer_exit
TESLA_DL_RECORD_LEN = 0x400  # Number of bytes expected from the server after performing a data transfer
TESLA_DL_DATA_FORMAT = 0x00  # High nibble: No Compression | Low nibble: No Encryption. Vals>0 are manufacturer specific
BLOCK_COUNTER_WIDTH_MOD = 256  # Block sequence counter gets 1 byte of width per spec, so must roll over after 255
MEM_PARAMS_FORMAT = 0x44    # High nibble: byte length of memorySize | Low nibble: byte length of memoryAddress
#                             Both are compiled as uint32_t in the C core library, so 4 bytes.


class Client(object):
    """
    Client wraps the udsClient (SWIG) and binds it to an arbitrary transport layer
    """

    def __init__(self, transport, logger=None, disable_threadsafety=False):
        """
        Initializes the udsClient DLLs, registers implemented CAN functions in the udsClient
        :param transport: <AbstractTransport> CAN Hardware instance that implements basic CAN hardware functions:
            Initialize
            get_node_info
            receive_frame
            transmit_frame
            clear_receive_queue
            _set_message_ids
            etc. (See AbstractTransport.py)
        :param logger: <Logger> TeslaUtilities message logger. One will be created if not provided.
        :param disable_threadsafety: <boolean> Disables threadsafety check
        """

        self.lock = threading.Lock()
        self.threadsafe = not disable_threadsafety

        self.filePointer = None

        if logger is None:
            logger = TeslaUtilities.get_logger()
        self._logger = logger

        self.transport = transport
        self.node = nodes.NONE

        # This only needs to get set once but it shouldn't be changing.
        # TODO: Move to somewhere it can just get set once.
        udsCore.caNetRegister(self.transport.get_node_info,
                              self.transport.transmit_frame,
                              self.transport.receive_frame,
                              self.transport.clear_receive_queue)

        # A handle is created and initialized for the given node.
        # The C core library calls get_node_info in abstract_transport to get the request/response IDs
        self.canHandle = udsCore.caNetGetHandle(int(self.node.nodeID))
        self.transport.set_node(self.node)

    def set_node(self, node):
        """
        set_node stores a the chosen nodes.Node and queues in the core library to the change
        :param node: <UDS.nodes.Node> a UDS Node. See UDS.nodes for more detail.
        """
        if node is self.node:
            self._logger.info("Already using this CAN node: \n    {0}".format(str(node)))
        else:
            if isinstance(node, nodes.Node):
                # Delete the old handle, since we're switching nodes
                udsCore.tpNetFreeHandle(self.canHandle)

                # Stop capturing messages for the old node
                self.transport.clear_node(self.node)

                self._logger.info("Setting CAN Node: \n    {0}".format(str(node)))
                self.node = node

                # A new handle is created and initialized for the given node.
                # The C core library calls get_node_info in abstract_transport to get the request/response IDs
                self.canHandle = udsCore.caNetGetHandle(int(self.node.nodeID))

                # Start capturing messages for the new node
                self.transport.set_node(self.node)

            else:
                msg = "Tried to set a node that isn't a UDS.nodes.Node object! {0}.".format(node)
                msg += "\n Refer to nodes/node.py for how to create custom nodes."
                self._logger.info(msg)
                raise TypeError(msg)

    ''' UDS '''

    @threadsafe_check
    def clear_dtc(self, dtcGroup):
        """
        Clear DTC clears the dtc requested. UNTESTED
        :param dtcGroup: <DTCMaskRecord_t *, see udsServices.c> "Refer to Table 237 in ISO_14229-1_2006-12"
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Clear DTC: {0}.".format(dtcGroup))  # TODO: Format this properly

        return udsCore.udsClearDiagnosticInformation(self.canHandle, dtcGroup)

    @threadsafe_check
    def control_dtc(self, dtcSettingType, recordLen, dtcSettingControlOptionRecord, responseRequired):
        """
        Control DTC sends a control command for a DTC. UNTESTED
        :param dtcSettingType: <uint8_t> "Refer to Table 82 of ISO_14229-1_2006-12."
        :param recordLen: <number> Size of DTCSettingControlOptionRecord buffer
        :param dtcSettingControlOptionRecord: <uint8_t *> This parameter record is user-optional
            and transmits data to a server when controlling the DTC setting. It
            can contain a list of DTCs to be turned on or off.
        :param responseRequired: <bool> whether to require a response, or not.
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Control DTC:")
        self._logger.info("    Setting Type: {0}.".format(dtcSettingType))
        self._logger.info("    Record Length: {0}.".format(recordLen))
        self._logger.info("    Setting Control Option: {0}.".format(dtcSettingControlOptionRecord))
        self._logger.info("    Response Required: {0}.".format(responseRequired))

        return udsCore.udsControlDTCSetting(self.canHandle,
                                            dtcSettingType,
                                            recordLen,
                                            dtcSettingControlOptionRecord,
                                            responseRequired)

    @threadsafe_check
    def read_dtc(self, requestData, outputDataLen):
        """
        Read DTC reads a DTC. UNTESTED
        :param requestData: <array of DTC_parameter_t (uint8)> the input data
        :param outputDataLen: <number> the length of the expected output
        :return errorCode, outData: <number>, <number or list of numbers> the error code response from UDS, output
        """
        self._logger.info("Read DTC:")
        self._logger.info("    Request: {0}.".format(requestData))
        self._logger.info("    Output Length: {0}.".format(outputDataLen))

        retrievedData = udsCore.new_uint8Array(outputDataLen)
        actualLength = udsCore.new_uint16p()

        errorCode = udsCore.udsReadDTCInformation(self.canHandle, outputDataLen, retrievedData,
                                                  actualLength, requestData)

        if errorCode != 0:
            self._logger.warning("Read DTC returned error: 0x{0:x}.".format(errorCode))

        outData = utils.from_byte_array(retrievedData, udsCore.uint16p_value(actualLength))

        udsCore.delete_uint16p(actualLength)
        udsCore.delete_uint8Array(retrievedData)

        return errorCode, outData

    @threadsafe_check
    def diagnostic_session(self, diagnosticSessionType, responseRequired):
        """
        Request a new diagnostic session:
            Default
            Programming
            Extended Diagnostic
            Safety System Diagnostic
        :param diagnosticSessionType: <number> the diagnostic session type  TODO: Maybe in an upper layer, use real type
        :param responseRequired: <bool> whether to require a response, or not.
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Diagnostic Session")
        self._logger.info("    Session Type: {0}".format(diagnosticSessionType))
        self._logger.info("    Response Required: {0}.".format(responseRequired))

        errorCode = udsCore.udsDiagnosticSessionControl(self.canHandle, diagnosticSessionType, responseRequired)
        self._logger.info("    errCode returned: {0}.".format(errorCode))
        return errorCode

    @threadsafe_check
    def ecu_reset(self, resetType, responseRequired):
        """
        Sends an ECU Reset Command
        :param resetType: <number> the type of reset TODO: Use a real type
        :param responseRequired: <bool> whether to require a response, or not.
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("ECU Reset:")
        self._logger.info("    Reset Type: {0}.".format(resetType.name))
        self._logger.info("    Response Required: {0}.".format(responseRequired))

        powerDownTime = udsCore.new_uint8p()

        errorCode = udsCore.udsECUReset(self.canHandle, resetType, powerDownTime, responseRequired)
        self._logger.info("    errCode returned: {0}.".format(errorCode))

        udsCore.delete_uint8p(powerDownTime)

        return errorCode

    @threadsafe_check
    def io_control(self, ioID, ioType, inputData, outputDataLen):
        """
        IO Control sends an Input/Output Control command
        :param ioID: <number> the io control ID
        :param ioType: <number> the IO Control type.  TODO: use a real type
            Return Control to ECU
            Reset to Default
            Freeze Current State
            Short Term Adjustment
        :param inputData: <array of uint8> the input data to send to the ECU.  Eventually converted into a byte array.
        :param outputDataLen: <number> Expected number of bytes to receive from server.
        :return errorCode, outData: <number>, <number or list of numbers> the error code response from UDS, output
        """
        self._logger.info("IO Control 0x{0:x}".format(ioID))
        self._logger.info("    Type: {0}.".format(ioType))
        self._logger.info("    Input: {0}.".format(inputData))
        self._logger.info("    Output Length: {0}.".format(outputDataLen))

        inputDataLength = len(inputData)
        inputData = utils.to_byte_array(inputData)
        outputData = udsCore.new_uint8Array(outputDataLen)
        actualLength = udsCore.new_uint16p()

        errorCode = udsCore.udsInputOutputControlByIdentifier(self.canHandle, ioID, ioType, inputDataLength, inputData,
                                                              outputDataLen, outputData, actualLength)

        if errorCode != 0:
            self._logger.warning("IO Control 0x{0:x} returned error: 0x{1:x}.".format(ioID, errorCode))

        if outputDataLen == 0:
            outData = None
        elif outputDataLen == 1:
            outData = utils.from_byte_array(outputData, outputDataLen)[0]
        else:
            outData = utils.from_byte_array(outputData, outputDataLen)

        udsCore.delete_uint8Array(inputData)
        udsCore.delete_uint8Array(outputData)
        udsCore.delete_uint16p(actualLength)

        return errorCode, outData

    @threadsafe_check
    def routine_control(self, rcID, rcType, inputData, outputDataLen):
        """
        Routine Control sends a Routine Control command
        :param rcID: <number> the routine control ID.
        :param rcType: <number> the type of routine to run.  TODO: Use a real type
            Start Routine
            Stop Routine
            Request Routine Results
        :param inputData: <array of uint8> the input data of the routine.
        :param outputDataLen: <int> the expected length of the output
        :return errorCode, outData: <number>, <number or list of numbers> the error code response from UDS, output
        """
        self._logger.info("Routine Control 0x{0:x}".format(rcID))
        self._logger.info("    Type: {0}.".format(rcType))
        self._logger.info("    Input: {0}.".format(inputData))
        self._logger.info("    Output Length: {0}.".format(outputDataLen))

        if not inputData:
            inputData = []
        inputDataLength = len(inputData)
        inputData = utils.to_byte_array(inputData)
        outputData = udsCore.new_uint8Array(outputDataLen)
        actualLength = udsCore.new_uint16p()

        errorCode = udsCore.udsRoutineControl(self.canHandle, rcType, rcID, inputDataLength, inputData,
                                              outputDataLen, outputData, actualLength)

        if outputDataLen == 0:
            outputData = None
            outData = None
        else:
            outData = utils.from_byte_array(outputData, outputDataLen)

        if errorCode != 0:
            self._logger.warning("Routine Control 0x{0:x} returned error: 0x{1:x}.".format(rcID, errorCode))
        else:
            self._logger.info("Routine Control returned: {}(size:{}).".format(outData, outputDataLen))

        udsCore.delete_uint8Array(inputData)
        udsCore.delete_uint8Array(outputData)
        udsCore.delete_uint16p(actualLength)

        return errorCode, outData

    @threadsafe_check
    def read_data(self, dataID, dataLen):
        """
        Read Data (by ID) sends the read data by ID command
        :param dataID: <number> the data ID to read
        :param dataLen: <number> the length of data to expect
        :return errorCode, outData: <number>, <number or list of numbers> the error code response from UDS, output
        """
        self._logger.info("Read Data 0x{0:x}".format(dataID))
        self._logger.info("    Data Length: {0}.".format(dataLen))

        outArray = udsCore.new_uint8Array(dataLen)
        numBytes = udsCore.new_uint16p()  # TODO: Double check this is what this actually does.
        errorCode = udsCore.udsReadDataByIdentifier(self.canHandle, dataID, dataLen, outArray, numBytes)

        if errorCode != 0:
            self._logger.warning("Read Data 0x{0:x} returned error: 0x{1:x}.".format(dataID, errorCode))

        outData = utils.from_byte_array(outArray, udsCore.uint16p_value(numBytes))

        udsCore.delete_uint8Array(outArray)
        udsCore.delete_uint16p(numBytes)

        return errorCode, outData

    @threadsafe_check
    def read_memory(self, memoryAddress, memorySize, outputDataLength):
        """
        Read Memory (By Address) sends the RMBA command.
        :param memoryAddress: <number> the address of the memory
        :param memorySize: <number> the size of the memory block
        :param outputDataLength: <number> number of bytes expected in return, sometimes different from memorySize
        :return errorCode, outData: <number>, <number or list of numbers> the error code response from UDS, output
        """
        self._logger.info("Read Memory:")
        self._logger.info("    Address: {0}.".format(memoryAddress))
        self._logger.info("    Size: {0}.".format(memorySize))
        self._logger.info("    Output Length: {0}.".format(outputDataLength))

        addressAndSizeFormatter = utils.get_address_size_format(memoryAddress, memorySize)

        dataRecord = udsCore.new_uint8Array(outputDataLength)  # Try using a pointer if this doesn't work.

        errorCode = udsCore.udsReadMemoryByAddress(self.canHandle, addressAndSizeFormatter, memoryAddress, memorySize,
                                                   outputDataLength, dataRecord)

        if errorCode != 0:
            self._logger.warning("Read Memory 0x{0:x} returned error: 0x{1:x}.".format(memoryAddress, errorCode))

        outData = utils.from_byte_array(dataRecord, outputDataLength)

        udsCore.delete_uint8Array(dataRecord)
        return errorCode, outData

    @threadsafe_check
    def write_data(self, dataID, dataToWrite):
        """
        Write Data (by ID) writes data to the ID specified.
        :param dataID: <number> the data ID to read
        :param dataToWrite: <array of uint8> the data to write
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Write Data 0x{0:x}".format(dataID))
        self._logger.info("    Data: {0}.".format(dataToWrite))

        recordLength = len(dataToWrite)
        dataRecord = utils.to_byte_array(dataToWrite)

        errorCode = udsCore.udsWriteDataByIdentifier(self.canHandle, dataID, recordLength, dataRecord)

        if errorCode != 0:
            self._logger.warning("Write Data 0x{0:x} returned error: 0x{1:x}.".format(dataID, errorCode))

        return errorCode

    @threadsafe_check
    def write_memory(self, memoryAddress, dataToWrite):
        """
        Write Memory (By Address) sends the WMBA command.
        :param memoryAddress: <number> the address of the memory
        :param dataToWrite: <array of uint8> the data to write
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Write Memory:")
        self._logger.info("    Address: {0}.".format(memoryAddress))
        # self._logger.info("    Size: {0}.".format(memorySize))
        self._logger.info("    Data: {0}.".format(dataToWrite))

        memorySize = len(dataToWrite)  # TODO: double check this will work.

        addressAndSizeFormatter = utils.get_address_size_format(memoryAddress, memorySize)

        dataRecord = utils.to_byte_array(dataToWrite)

        errorCode = udsCore.udsWriteMemoryByAddress(self.canHandle, addressAndSizeFormatter, memoryAddress,
                                                    memorySize, dataRecord)

        if errorCode != 0:
            self._logger.warning("Write Memory 0x{0:x} returned error: 0x{1:x}.".format(memoryAddress, errorCode))

        return errorCode

    @threadsafe_check
    def security_access(self, level):
        """
        Get Security Access from the ECU. Multistep process.
        :param level: <number> the level of security access.  TODO: use a real type.
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.info("Requesting Security Access.")
        self._logger.info("    Level: {0}.".format(level))

        receiveSeed = udsCore.new_uint8Array(MAX_SEED_SIZE)
        transmitKey = udsCore.new_uint8Array(MAX_SEED_SIZE)
        numBytes = udsCore.new_uint16p()

        errorCode = udsCore.udsSecurityAccessRequestSeed(self.canHandle, level, MAX_SEED_SIZE,
                                                         receiveSeed, numBytes)
        if errorCode == 0:
            seedLen = udsCore.uint16p_value(numBytes)
            for index in xrange(0, seedLen):
                key = udsCore.uint8Array_getitem(receiveSeed, index) ^ KEYGEN_MASK  # key = seed xor magic
                udsCore.uint8Array_setitem(transmitKey, index, key)
            errorCode = udsCore.udsSecurityAccessSendKey(self.canHandle, level + 1, seedLen, transmitKey)

            if errorCode != 0:
                self._logger.warning("Security Access Level {0} returned error: 0x{1:x}."
                                     .format(level, errorCode))
        elif errorCode == 0x303:  # Magic
            self._logger.warning("Already have security access.")
        else:
            self._logger.warning("Security Access Request Level {0} returned error: 0x{1:x}."
                                 .format(level, errorCode))

        udsCore.delete_uint8Array(receiveSeed)
        udsCore.delete_uint8Array(transmitKey)
        udsCore.delete_uint16p(numBytes)

        return errorCode

    @threadsafe_check
    def tester_present(self, responseRequired):
        """
        Tester Present sends out the Tester Present message
        :param responseRequired: <bool> whether to require a response or not
        :return errorCode: <number> the error code response from UDS
        """
        # These are in debug because a TP thread will annihilate a log otherwise.
        self._logger.debug("Tester Present.")
        self._logger.debug("    Response Required: {0}.".format(responseRequired))

        errorCode = udsCore.udsTesterPresent(self.canHandle, responseRequired)

        if errorCode != 0:
            self._logger.warning("Tester Present returned error: 0x{0:x}.".format(errorCode))
        return errorCode

    ''' Download Helpers '''

    def wait_for_boot_id(self, periodic=False, bootInApp=False):
        """
        Wait for boot ID reads the CAN hardware looking for a boot ID. Uses specified node if none given.
        Passes through to transport layer as implementations may differ.
        :param periodic: <bool> True if the ECU is expected to send several boot messages periodically.
        :param bootInApp: <bool> True if ECU is expected to send the message from App
        :param bootID: <number> optional CAN ID of the boot message.  Uses internal node data if not supplied.
        :return outData: <list of numbers> bootID output
        """

        return self.transport.wait_for_boot_id(self.node, periodic, bootInApp)

    def request_download_init(self, memoryAddress,
                              memorySize=DL_CHUNK_SIZE,
                              recordLength=TESLA_DL_RECORD_LEN,
                              dataFormatID=TESLA_DL_DATA_FORMAT):
        """
        Request Download Init(ialization)
        :param memoryAddress: <number> The start memory address from the hex file.
        :param memorySize: <number> Size of the chunk to transmit before request_transfer_exit will be called
        :param recordLength: <number> The expected number of bytes returned from the ECU.
        :param dataFormatID: <number> the data format ID.  Compression Nibble | Encryption Nibble
        :return errorCode, responseSize: <number, number> the errorCode of the Request, and the size allowed for xfer
        """
        self._logger.debug("Request Download Init.")  # TODO: Consider not logging during this section to improve speed
        self._logger.debug("    Memory Address: 0x{0:x}.".format(memoryAddress))
        self._logger.debug("    Memory Size: {0}.".format(memorySize))
        self._logger.debug("    Record Length: {0}.".format(recordLength))
        self._logger.debug("    Data Format: 0x{0:x}.".format(dataFormatID))

        dataRecord = udsCore.new_uint8Array(recordLength * 8)
        actualLength = udsCore.new_uint16p()

        errorCode = udsCore.udsRequestDownload(self.canHandle, dataFormatID, MEM_PARAMS_FORMAT,
                                               memoryAddress, memorySize, recordLength, dataRecord, actualLength)

        if errorCode != 0:
            self._logger.warning("Request Download Init returned error: 0x{0:x}.".format(errorCode))

        responseSize = 0
        for i in xrange(0, udsCore.uint16p_value(actualLength) - 1):
            responseSize <<= i * 8
            responseSize |= udsCore.uint8Array_getitem(dataRecord, i + 1)

        udsCore.delete_uint8Array(dataRecord)
        udsCore.delete_uint16p(actualLength)

        return errorCode, responseSize - 2  # TODO: Not sure why we have to subtract 2.

    def transfer_data(self, startAddress, serverBufferSize, memorySize, mau=None):
        """
        Transfer Data is a UDS Download helper function to transfer data.
        :param startAddress: <number> the start address of the file chunk we are transferring.
        :param serverBufferSize: <number> the size of the buffer we can fill.
        :param memorySize: <number> Not really sure if this is used, but supposedly the size of the memory.
        :return errorCode: <number> the error code response from UDS
        """

        if mau is None:
            mau = self.node.mau

        self._logger.debug("Transfer Data")  # TODO: Consider not logging during this section to improve speed

        requestLength = serverBufferSize
        responseLength = 0

        transferResponseParameterRecord = udsCore.new_uint8Array(responseLength)

        bytesLeft = memorySize
        blockSequenceCounter = 0x01  # Initialize block sequence counter

        errorCode = 0

        while bytesLeft > 0:

            if bytesLeft >= serverBufferSize:
                requestLength = serverBufferSize
            else:
                requestLength = bytesLeft

            endAddress = startAddress + requestLength / mau
            transferRequestParameterRecord = self.get_data(startAddress, endAddress, mau)

            errorCode = udsCore.udsTransferData(self.canHandle, blockSequenceCounter, requestLength,
                                                transferRequestParameterRecord, responseLength,
                                                transferResponseParameterRecord)

            if errorCode != 0:
                self._logger.warning("Transfer Data returned error: 0x{0:x}.".format(errorCode))
                self._logger.warning("Having to resend a packet.")

                # TODO: Figure out a scheme for multiple retries of a packet without causing sequence counter error!
                # Or exiting the download if the second try fails too

                errorCode = udsCore.udsTransferData(self.canHandle, blockSequenceCounter, requestLength,
                                                    transferRequestParameterRecord, responseLength,
                                                    transferResponseParameterRecord)

                udsCore.delete_uint8Array(transferRequestParameterRecord)
                if errorCode != 0:
                    msg = "2nd attempt failed, Transfer Data returned error: 0x{0:x}.".format(errorCode)
                    self._logger.error(msg)
                    raise ValueError(msg)
            else:
                startAddress += requestLength / mau
                bytesLeft -= serverBufferSize

            # I0 increment block sequence counter, wrap around as necessary
            blockSequenceCounter = (blockSequenceCounter + 1) % BLOCK_COUNTER_WIDTH_MOD

        if errorCode != 0:
            self._logger.warning("Transfer Data returned error: 0x{0:x}.".format(errorCode))

        udsCore.delete_uint8Array(transferResponseParameterRecord)

        return errorCode

    def request_transfer_exit(self):
        """
        Request Transfer Exit finalizes a data transfer.
        :return errorCode: <number> the error code response from UDS
        """
        self._logger.debug("Request Transfer Exit.")

        requestLength = 0
        transferRequestParameterRecord = udsCore.new_uint8Array(requestLength)
        responseLength = 0
        transferResponseParameterRecord = udsCore.new_uint8Array(responseLength)

        errorCode = udsCore.udsRequestTransferExit(self.canHandle, requestLength, transferRequestParameterRecord,
                                                   responseLength, transferResponseParameterRecord)

        if errorCode != 0:
            self._logger.warning("Request Transfer Exit returned error: 0x{0:x}.".format(errorCode))

        udsCore.delete_uint8Array(transferRequestParameterRecord)
        udsCore.delete_uint8Array(transferResponseParameterRecord)

        return errorCode

    def parse_data_get_size(self, filename, module=UdsModuleID.UDS_FLASH_APPLICATION):
        """
        TODO: should this really be in client?

        Parse Data Get Size parses the file given by filename and returns data necessary for downloading.
            Sets filePointer.
        :param filename: <string> full path to the filename
        :return totalSize, startAddress: <number, number> the total size of the file, the start address.
        """
        self._logger.debug("Parse Data Get Size.")

        # TODO: Figure out which other possible modules to flash will not have MAU >1 even if the main ECU does.
        if module not in [UdsModuleID.UDS_CPLD, UdsModuleID.UDS_CURRENT_SHUNT]:
            module_mau = self.node.mau
            if self.node.mau == 1:
                self.filePointer = Hex()
            elif self.node.mau == 2:
                self.filePointer = Hex16bit()
            else:
                msg = "Unsupported MAU in Parse Data Get Size: {0}.".format(self.node.mau)
                self._logger.error(msg)
                raise Exception(msg)
        else:
            self.filePointer = Hex()
            module_mau = 1

        self.filePointer.loadfile(filename, "hex", mau_in=module_mau, mau_out=module_mau)
        regions_info = self.filePointer.get_regions_info()

        for i, (address, length) in enumerate(regions_info):
            self._logger.debug("*** Region {0:d} ***".format(i))
            self._logger.debug("Start Address: 0x{0:x}.".format(address/module_mau))
            self._logger.debug("End Address: 0x{0:x}.".format((address+length)/module_mau))
            self._logger.debug("Total Size: 0x{0:x}.".format(length/module_mau))

        return regions_info

    def get_data(self, startAddress, endAddress, mau=None):
        """
        Get Data chunks the hex file for transmission
        :param startAddress: <number>
        :param endAddress: <number>
        :return data: <array of uint8> data array chunked from file based on address.
        """

        if mau is None:
            mau = self.node.mau

        self._logger.debug("Get Data for Address Range: 0x{0:x} - 0x{1:x}.".format(startAddress, endAddress))
        data = udsCore.new_uint8Array((endAddress - startAddress)*mau)

        indexDataArray = 0
        indexData = 0

        if mau == 1:
            index = 0
            for i in range(startAddress, endAddress):
                udsCore.uint8Array_setitem(data, index, self.filePointer[i])
                index += 1
        elif mau == 2:  # These things make it complicated.
            dataArray = self.filePointer.tobinarray(start=startAddress, end=endAddress)

            for i in xrange(startAddress, endAddress):
                temp = int(dataArray[indexDataArray] >> 0) & int(0xff)
                udsCore.uint8Array_setitem(data, indexData, temp)
                temp = int(dataArray[indexDataArray] >> 8) & int(0xff)
                udsCore.uint8Array_setitem(data, (indexData + 1), temp)
                indexDataArray += 1
                indexData += 2
        else:
            msg = "Unsupported MAU in Get Data: {0}.".format(mau)
            self._logger.error(msg)
            raise Exception(msg)

        return data

    ''' Other stuff '''

    def close(self):
        """
        Destructor.  Handles the release of SWIG stuff.
        """
        try:
            udsCore.tpNetFreeHandle(self.canHandle)
        except:
            self._logger.error("Could not free the CAN handle.")

    def __del__(self):
        """
        Destructor interface.
        """
        self.close()


if __name__ == '__main__':
    print __doc__
    print Client.__doc__
