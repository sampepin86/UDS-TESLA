"""
BusID.py
Created on Jun 27, 2016

@author: tbell

@description: BusID is the definition and container for Known Tesla UDS Bus IDs.
              BusID's are really a gateway concept, not part of the UDS or CAN standard.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.
"""
from enum import IntEnum, unique


# noinspection PyPep8
@unique
class BusID(IntEnum):
    """
    The Bus IDs of the different Buses on the vehicle/powerwall/supercharger
    """
    UDS_BUS_NONE    = -1
    UDS_BUS_DIAG    = 0
    UDS_BUS_BDY     = 1
    UDS_BUS_PT      = 2
    UDS_BUS_BFT     = 3
    UDS_BUS_PS      = 4
    UDS_BUS_CH      = 5
    UDS_BUS_ETH     = 6
    UDS_BUS_SC      = 7
    UDS_BUS_TH      = 8
    UDS_BUS_FC      = 9

