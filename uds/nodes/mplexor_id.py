"""
Mplexor.py
Created on Jun 27, 2016

@author: tbell

@description: Mplexor is the definition and container for Known Tesla UDS Mplexors.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.

"""
from enum import IntEnum, unique


@unique
class Mplexor(IntEnum):
    UNKNOWN_MPLEXOR = 0
    TESLA_INFOMSG_APP_CRC_MPLEXOR = 0x0D
    TESLA_INFOMSG_BOOT_CRC_MPLEXOR = 0X14
    TESLA_INFOMSG_VAR_CRC_MPLEXOR = 0x16
    TESLA_INFOMSG_VERSION_MPLEXOR = 0x13
    TESLA_INFOMSG_SUBCOMP1_VER_MPLEXOR = 0x10
    TESLA_INFOMSG_SUBCOMP2_VER_MPLEXOR = 0x17
    TESLA_INFOMSG_SUBCOMP3_VER_MPLEXOR = 0x18
