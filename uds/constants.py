"""
Created on Mon Apr 4, 2016
Constants file for Advanced CAN

@author: jpetrie

@description: Constants to make some UDS features easier to use.
"""

ID_LENGTHS = {
    0x101: 3,
    0x102: 1,
    0x103: 10,
    0xf011: 128,
    0xf012: 20,
    0xf013: 14,
    0xf014: 20,
    0xf015: 14,
    0xf016: 1,
    0xf017: 4,
    0xf018: 128,
    0xf01a: 4,
    0xf01c: 1,
    0xf01d: 2,
    0xf01e: 2,
    0xf01f: 2,  # TODO <BD> check to make sure this is right
    0xf020: 2,  # TODO <BD> check to make sure this is right
    0xf180: 19,
    0xf181: 19,
}

ID_NAME_STRINGS = {
    0x101: "Component And Firmware Type",
    0x102: "Module to Program",
    0x103: "Tool Serial Number",
    0xf011: "Manufacturing Block",
    0xf012: "Board Part Number",
    0xf013: "Board Serial Number",
    0xf014: "Package Part Number",
    0xf015: "Package Serial Number",
    0xf016: "Genealogy Version Number",
    0xf017: "Genealogy CRC",
    0xf018: "Genealogy Block",
    0xf019: "Calibration Version Number",
    0xf01a: "Calibration CRC",
    0xf01c: "Assembly ID",
    0xf01d: "Usage ID",
    0xf01e: "Sub Usage ID",
    0xf01f: "EEPROM Block Status",  # TODO check to make sure this is right
    0xf020: "Calibration Block",  # TODO check to make sure this is right
    0xf180: "Bootloader Version",
    0xf181: "App Version",
}

# Constants

''' 0x101 (running module) message key '''
APPLICATION_TALKING = 0x00
BOOTLOADER_TALKING = 0x01
UPDATER_TALKING = 0x02

''' UDS library reponse codes '''
CAN_UNEXP_PDU_01 = 0xA

''' UDS Negative Response Codes '''
SERVICE_NOT_SUPPORTED = 0x11
SUBFUNCTION_NOT_SUPPORTED = 0x12
REQUEST_OUT_OF_RANGE = 0x31
SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F

''' _getData value '''
DEFAULT_BUFFER_SIZE = 0x100

SECURITY_ACCESS_PROTOCOL_VERSION = 5  # was 3
DOWNLOAD_PROTOCOL_VERSION = 5
GENEALOGY_BLOCK_LENGTH = 128

DASHES_LINE = "---------------------------------------------------"
TAB_STRING = "                                "
DASH_STRING = DASHES_LINE + "\n" + TAB_STRING + DASHES_LINE + "\n" + TAB_STRING + DASHES_LINE

MAGIC_DOWNLOAD_WAIT = 0.2  # Seconds

''' Start of TI bootloader flash address '''
TESLA_TI_BEGIN_FLASH_ADDRESS = 0x3F7FF6

DEFAULT_READ_TIMEOUT_SECONDS = 10
DEFAULT_READ_WAIT_SECONDS = 0.2
