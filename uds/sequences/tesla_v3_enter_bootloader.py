"""
Created on Tues Aug 2 2016

@author: Tyler Bell <tbell@tesla.com>
"""

# Base Python
import sys
import threading
import os
import time

# Tesla Python
import uds.utils as utils
import uds.nodes as nodes
import uds.constants as constants
from uds.typedefs import UdsResetType, UdsModuleID, UdsSessionType
import uds.TeslaUtilities

UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE = 0x0101
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_INPUT_LENGTH  = 0
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_OUTPUT_LENGTH  = 3
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BYTE = 1
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_APPLICATION = 0
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BOOTLOADER = 1
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BOOTLOADER_UPDATER = 2
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_SECONDARY_BOOTLOADER = 3
UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_PROTOCOL_VERSION_BYTE = 2



def UDS_utility_getCompAndFwType(client):
    """

    :param client: UDS.Client.client instance
    :return: (*compAndFwTyp, *protoVer) | (uint8_t, uint8_t)
    """
    success, DID_data = client.read_data(UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE,
                                         UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_OUTPUT_LENGTH)
    if success:
        compAndFwTyp = DID_data[UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BYTE]
        protoVer = DID_data[UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_PROTOCOL_VERSION_BYTE]

        return (compAndFwTyp, protoVer, )

    return False


def tesla_v3_enterBootloader(client, logger=None):
    """
    Reboots the node to the bootloader
    :param client: <UDS.client.Client> instance
    :param logger: logger object, or false to not log
    :return error_code: <number> the resultant error code.
    """

    # make a logger if we didn't get one
    if logger is None:
        logger = TeslaUtilities.get_logger()
    elif not logger:
        # if you specified False, it means you don't want to log. We're still going to stderr errors though.
        # i <3 hacking python
        logger = lambda: 0
        logger.info = lambda *x: 0
        logger.debug = lambda *x: 0
        logger.error = sys.stderr.write

    # set up the tp thread
    # make a flag to make it join-able
    abort_tp_thread = False
    pause_tps = False

    # make a target
    def _tester_present_thread():
        while not abort_tp_thread:
            if not pause_tps:
                start = time.time()
                client.tester_present(False)
                diff = time.time() - start
                time.sleep(max(0.09 - diff, 0.01))

    # start it
    tp_thread = threading.Thread(target=_tester_present_thread)
    tp_thread.start()
    try:
        logger.info("Rebooting ECU...")
        counter = 0
        responseRequired = False
        bootloaderUDSProtocolVersion = 5
        tpMessageCount = 500
        componentType = 0

        compAndFwTyp, protoVer = UDS_utility_getCompAndFwType(client)
        if protoVer > 5:
            responseRequired = True
            tpMessageCount = 0

        if client.ecu_reset(UdsResetType.HARD_RESET, responseRequired) == 0:
            time.sleep(0.010)
            logger.info("Sending tester present messages for 5 seconds...")
            start = time.time()
            while time.time() < start + 5:
                counter += 1
                client.tester_present(False)
                time.sleep(0.010)

            logger.info("Confirming that communication link still works...")

            if client.tester_present(True) == 0:
                logger.info("Success.\n")
                return True
    finally:
        abort_tp_thread = True
        tp_thread.join()

    return False
