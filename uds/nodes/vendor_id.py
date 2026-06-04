"""
Vendor.py
Created on Jun 27, 2016

@author: tbell

@description: VendorIDs is the definition and container for Known Tesla (and vendor) Vendor IDs.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.
"""
from enum import IntEnum, unique


@unique
class VendorID(IntEnum):
    """
    Enum container of Vendor IDs. See Firmware Repo for more info.
    """
    UDS_VENDOR_BAOLONG = 0
    UDS_VENDOR_BITRON = 1
    UDS_VENDOR_BOSCH = 2
    UDS_VENDOR_CONTINENTAL = 3
    UDS_VENDOR_DELPHI = 4
    UDS_VENDOR_HALLA = 5
    UDS_VENDOR_JLR = 6
    UDS_VENDOR_KOSTAL = 7
    UDS_VENDOR_PANASONIC = 8
    UDS_VENDOR_PEKTRON = 9
    UDS_VENDOR_TESLA = 10
    UDS_VENDOR_BOSCH_TESLA_SPEC = 11
    UDS_VENDOR_CONTI_TESLA_SPEC = 12
    UDS_VENDOR_VALEO = 13
    UDS_VENDOR_HELLA = 14
    UDS_VENDOR_UNKNOWN = 15
