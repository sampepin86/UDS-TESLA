"""
Created on Thurs Aug 4 2016

@author: Tyler Bell <tbell@tesla.com>
"""

from utils import *
from uds_protocol_versions import *
from prepare_ecu import UDS_Operation_prepareTeslaECU


def getBootloaderVersion(client, isGit, logger=None):
    """
    shamelessly stolen from :
    https://stash.teslamotors.com/projects/TBX/repos/lib-vehicle/commits/625c9ca943c8870b1351e985284c7939098e1ae5#cpp/Uds/Uds.cpp

    This is currently implemented to support Toolbox 2.0 without modification. This is not a great idea.
    Expect implemenation to change significantly as time allows. For one, the isGit parameter is kind of silly.

    :param client: <UDS.client>
    :param isGit: <bool>
    :param logger: <logger object>
    :return:
    """

    if client.node.vendorID != VendorID.UDS_VENDOR_TESLA:
        raise Exception("This only applies to Tesla ECUs")

    priv = UDS_init_privateVariablesForDownload(client, UdsModuleID.UDS_FLASH_APPLICATION,
                                                UDS_TESLA_DOWNLOAD_PROTOCOL_VERSION_LATEST,
                                                False, False, False, logger)

    bootloaderInfo = UDS_Operation_prepareTeslaECU(client, priv, logger)
    if bootloaderInfo:
        return bootloaderInfo['gitHash'] if isGit else bootloaderInfo['SVN_revision']
    else:
        return False
