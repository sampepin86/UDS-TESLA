"""
Created on Tues Aug 2 2016

@author: Tyler Bell <tbell@tesla.com>
all this shamelessly stolen from:
https://stash.teslamotors.com/projects/TBX/repos/lib-vehicle/commits/625c9ca943c8870b1351e985284c7939098e1ae5#cpp/Uds/client/UDS_Download_Operations.c

"""

# Base Python

from struct import unpack

from uds.nodes.node_id import NodeID
from uds.nodes.vendor_id import VendorID
from uds.typedefs import *
from constants import *


def UDS_utility_getCompAndFwType(client):
    """
    :param client: UDS.Client.client instance
    :return: (*compAndFwTyp, *protoVer) | (uint8_t, uint8_t)
    """
    errCode, DID_data = client.read_data(UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE,
                                         UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_OUTPUT_LENGTH)
    if errCode == 0:
        compAndFwTyp = DID_data[UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BYTE]
        protoVer = DID_data[UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_PROTOCOL_VERSION_BYTE]

        return compAndFwTyp, protoVer,

    return False


def UDS_utility_talkToBootloader(client, logger):
    """
    bool UDS_utility_talkToBootloader(UDS_vars_S *privPtr)
    :return:
    """

    compAndFwTypeVer = UDS_utility_getCompAndFwType(client)
    if not compAndFwTypeVer:
        return False
    else:
        compAndFwType = compAndFwTypeVer[0]
        protoVer = compAndFwTypeVer[1]

        if compAndFwType == UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_APPLICATION:
            logger.error("Oops! Talking to application but need to talk to bootloader. ABORTING!\n")
            return False
        elif compAndFwType == UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BOOTLOADER:
            logger.error("Confirmed that we are talking to Bootloader... Success.\n")
        elif compAndFwType == UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_BOOTLOADER_UPDATER:
            logger.error("Oops! Talking to boot updater but need to talk to bootloader. ABORTING!\n")
            return False
        elif compAndFwType == UDS_TESLA_ALL_DID_COMPONENT_AND_FIRMWARE_TYPE_SECONDARY_BOOTLOADER:
            logger.error("Oops! Talking to secondary bootloader but need to talk to bootloader. ABORTING!\n")
            return False
        else:
            logger.error("Oops! Not sure what we're talking to, but it's certainly not the bootloader. ABORTING!\n")
            return False

    return protoVer


def UDS_utility_getBootloaderVersion(client, priv, logger=None):
    """
    bool UDS_utility_getBootloaderVersion(
    UDS_vars_S *privPtr, UDS_bootloaderVersionInfo_t *bootloaderVersionInfo)
    """
    errCode, DID_data = client.read_data(UDS_TESLA_ALL_DID_BOOTLOADER_VERSION,
                                         UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_OUTPUT_LENGTH_V4)
    if errCode != 0:
        return None

    bootloaderVersionInfo = {}
    if priv['uds_download_protocol_version'] == 3:
        if (len(DID_data) != UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_OUTPUT_LENGTH_V3) \
                or (DID_data[0] != UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_FIXED_INFO_BYTE):
            logger.info(
                "Version 3 information did not check out! Might be an intermediate (non-released) bootloader build!")
            if priv['flashBootUpdater']:
                logger.info(
                    "Since we are flashing a boot updater, ignore the result of the above check and keep going.")
                return {}
            else:
                logger.info("Tool will not allow application download until bootloader is updated!")
                return None

        logger.info("Platform type: {}", DID_data[1])
        logger.info("Platform Version: {}.{}.{}".format(DID_data[2], DID_data[3], DID_data[4]))
        logger.info("Component Version: {}.{}.{}".format(DID_data[5], DID_data[6], DID_data[7]))
        logger.info("Component Hardware Revision: {}\n".format(DID_data[8]))

        # store the hardware revision
        bootloaderVersionInfo['bootSignature'] = (DID_data[8], 0)

    elif priv['uds_download_protocol_version'] in (4, 5, 6):
        if (len(DID_data) != UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_OUTPUT_LENGTH_V4) \
                or (DID_data[0] != UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_FIXED_INFO_BYTE):

            logger.info("Version 4/5 information did not check out! "
                        "Might be an intermediate (non-released) "
                        "bootloader build!\nPlease update bootloader "
                        "before proceeding.")

            if priv['flashBootUpdater']:
                logger.info("Since we are flashing a boot updater, "
                            "ignore the result of the above check "
                            "and keep going.")
                return {}
            else:
                logger.info("Tool will not allow application "
                            "download until bootloader is updated!")
                return None

        logger.info("Bootloader hardware ID signature: ")

        if priv['uds_download_protocol_version'] == 4:
            bootloaderVersionInfo['bootSignature'] = ''.join(str(c) for c in DID_data[1:9])
            logger.info("%s\n", bootloaderVersionInfo['bootSignature'])
        elif priv['uds_download_protocol_version'] in (5, 6):
            bootloaderVersionInfo['componentID'] = \
                unpack('>H', DID_data[UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_COMP_ID_OFFSET:UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_COMP_ID_OFFSET + 2])[0]
            logger.info("Bootloader component ID: {}".format(bootloaderVersionInfo['componentID']))
            bootloaderVersionInfo['pcbID'] = DID_data[UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_PCBA_ID_OFFSET]
            logger.info("Bootloader PCB ID: {}".format(bootloaderVersionInfo['pcbID']))
            bootloaderVersionInfo['assemblyID'] = DID_data[UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_ASSEMBLY_ID_OFFSET]
            logger.info("Bootloader assembly ID: {}".format(bootloaderVersionInfo['assemblyID']))
            bootloaderVersionInfo['usageID'] = \
                unpack('>H', DID_data[UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_USAGE_ID_OFFSET:UDS_TESLA_ALL_DID_BOOTLOADER_VERSION_V5_USAGE_ID_OFFSET + 2])[0]
            logger.info("Bootloader usage ID: %u\n".format(bootloaderVersionInfo['usageID']))

        potential_SVN_revision = unpack('>L', DID_data[9:12])[0]
        if potential_SVN_revision < SVN_REVISION_MAX_GIT_HASH_ABOVE_THIS:
            bootloaderVersionInfo['SVN_revision'] = potential_SVN_revision
            bootloaderVersionInfo['SVN_URL_hash'] = unpack('>L', DID_data[13:16])[0]
            logger.info("Bootloader SVN revision: {}".format(bootloaderVersionInfo['SVN_revision']))
            logger.info("Bootloader SVN URL hash: {}".format(bootloaderVersionInfo['SVN_URL_hash']))
        else:
            bootloaderVersionInfo['gitHash'] = unpack('>Q', DID_data[9:16])[0]
            logger.info("Bootloader git hash: {:#x}".format(bootloaderVersionInfo['gitHash']))

        bootloaderVersionInfo['build_configuration_ID'] = unpack('>H', DID_data[17:18])[0]
        logger.info("Bootloader build configuration ID: {}".format(bootloaderVersionInfo['build_configuration_ID']))

    return bootloaderVersionInfo


def IS_BHX_NODE(_node):
    return NodeID.UDS_NODE_SCCM == _node.nodeID or NodeID.UDS_NODE_OCS == _node.nodeID


def UDS_findDataBytesPerAddress(nodeId, moduleToProgram):
    """
    UDS_byte_t UDS_findDataBytesPerAddress(
        UDS_byte_t node, UDS_byte_t moduleToProgram)
    """
    numBytes = 1

    oneByteNodes = [
        NodeID.UDS_NODE_BDY,
        # Supercharger VI nodes start */
        NodeID.UDS_NODE_CHG01VI,
        NodeID.UDS_NODE_CHG02VI,
        NodeID.UDS_NODE_CHG03VI,
        NodeID.UDS_NODE_CHG04VI,
        NodeID.UDS_NODE_CHG05VI,
        NodeID.UDS_NODE_CHG06VI,
        NodeID.UDS_NODE_CHG07VI,
        NodeID.UDS_NODE_CHG08VI,
        NodeID.UDS_NODE_CHG09VI,
        NodeID.UDS_NODE_CHG10VI,
        NodeID.UDS_NODE_CHG11VI,
        NodeID.UDS_NODE_CHG12VI,
        # Supercharger VI nodes end 
        NodeID.UDS_NODE_CHADA,
        NodeID.UDS_NODE_CHGVI,
        NodeID.UDS_NODE_CHGSVI,
        NodeID.UDS_NODE_DDM,
        NodeID.UDS_NODE_PDM,
        NodeID.UDS_NODE_SEC,
        NodeID.UDS_NODE_SUN,
        NodeID.UDS_NODE_LFT,
        NodeID.UDS_NODE_DHFD,
        NodeID.UDS_NODE_DHFP,
        NodeID.UDS_NODE_DHRD,
        NodeID.UDS_NODE_DHRP,
        NodeID.UDS_NODE_HNDFD,
        NodeID.UDS_NODE_HNDFP,
        NodeID.UDS_NODE_HNDRD,
        NodeID.UDS_NODE_HNDRP,
        NodeID.UDS_NODE_EAS,
        NodeID.UDS_NODE_EPAS,
        NodeID.UDS_NODE_ESP,
        NodeID.UDS_NODE_MSM,
        NodeID.UDS_NODE_MSMD,
        NodeID.UDS_NODE_MSMP,
        NodeID.UDS_NODE_OCS,
        NodeID.UDS_NODE_PTC,
        NodeID.UDS_NODE_RCCM,
        NodeID.UDS_NODE_SCCM,
        NodeID.UDS_NODE_SDM,
        NodeID.UDS_NODE_THC,
        NodeID.UDS_NODE_TPMS,
        NodeID.UDS_NODE_HVBS,
        NodeID.UDS_NODE_DCDC,
    ]

    tossUpNodes = [
        NodeID.UDS_NODE_BMS,
        NodeID.UDS_NODE_SSD1,
        NodeID.UDS_NODE_SSD2,
        NodeID.UDS_NODE_SSD3,
        NodeID.UDS_NODE_SSD4,
        NodeID.UDS_NODE_SSD5,
        NodeID.UDS_NODE_SSD6,
        NodeID.UDS_NODE_SSD7,
        NodeID.UDS_NODE_SSD8,
        NodeID.UDS_NODE_SSD9,
        NodeID.UDS_NODE_SSD10,
        NodeID.UDS_NODE_CHGPH1,
        NodeID.UDS_NODE_CHGPH2,
        NodeID.UDS_NODE_CHGPH3,
        NodeID.UDS_NODE_CHGSPH1,
        NodeID.UDS_NODE_CHGSPH2,
        NodeID.UDS_NODE_CHGSPH3,
        # Supercharger phase nodes start 
        NodeID.UDS_NODE_CHG01PH1,
        NodeID.UDS_NODE_CHG02PH1,
        NodeID.UDS_NODE_CHG03PH1,
        NodeID.UDS_NODE_CHG04PH1,
        NodeID.UDS_NODE_CHG05PH1,
        NodeID.UDS_NODE_CHG06PH1,
        NodeID.UDS_NODE_CHG07PH1,
        NodeID.UDS_NODE_CHG08PH1,
        NodeID.UDS_NODE_CHG09PH1,
        NodeID.UDS_NODE_CHG10PH1,
        NodeID.UDS_NODE_CHG11PH1,
        NodeID.UDS_NODE_CHG12PH1,
        NodeID.UDS_NODE_CHG01PH2,
        NodeID.UDS_NODE_CHG02PH2,
        NodeID.UDS_NODE_CHG03PH2,
        NodeID.UDS_NODE_CHG04PH2,
        NodeID.UDS_NODE_CHG05PH2,
        NodeID.UDS_NODE_CHG06PH2,
        NodeID.UDS_NODE_CHG07PH2,
        NodeID.UDS_NODE_CHG08PH2,
        NodeID.UDS_NODE_CHG09PH2,
        NodeID.UDS_NODE_CHG10PH2,
        NodeID.UDS_NODE_CHG11PH2,
        NodeID.UDS_NODE_CHG12PH2,
        NodeID.UDS_NODE_CHG01PH3,
        NodeID.UDS_NODE_CHG02PH3,
        NodeID.UDS_NODE_CHG03PH3,
        NodeID.UDS_NODE_CHG04PH3,
        NodeID.UDS_NODE_CHG05PH3,
        NodeID.UDS_NODE_CHG06PH3,
        NodeID.UDS_NODE_CHG07PH3,
        NodeID.UDS_NODE_CHG08PH3,
        NodeID.UDS_NODE_CHG09PH3,
        NodeID.UDS_NODE_CHG10PH3,
        NodeID.UDS_NODE_CHG11PH3,
        NodeID.UDS_NODE_CHG12PH3,
    ]

    twoByteNodes = [
        NodeID.UDS_NODE_CHG,
        NodeID.UDS_NODE_CHGS,
        NodeID.UDS_NODE_CP,
        NodeID.UDS_NODE_EPB,
        NodeID.UDS_NODE_EPBM,
        NodeID.UDS_NODE_SCM,
        NodeID.UDS_NODE_SCS,
        # Supercharger nodes start
        NodeID.UDS_NODE_SC1,
        NodeID.UDS_NODE_SC2,
        NodeID.UDS_NODE_SC3,
        NodeID.UDS_NODE_SC4,
        NodeID.UDS_NODE_SC5,
        NodeID.UDS_NODE_SC6,
        NodeID.UDS_NODE_SC7,
        NodeID.UDS_NODE_SC8,
        NodeID.UDS_NODE_SC9,
        NodeID.UDS_NODE_SC10,
        NodeID.UDS_NODE_SC11,
        NodeID.UDS_NODE_SC12,
        # Supercharger nodes end 
        NodeID.UDS_NODE_IC,
        NodeID.UDS_NODE_DI,
        NodeID.UDS_NODE_DIS,
        NodeID.UDS_NODE_PM,
        NodeID.UDS_NODE_PMS,
    ]

    if nodeId in oneByteNodes:
        numBytes = 1  # Supercharger phase nodes end
    elif nodeId in tossUpNodes:
        if moduleToProgram in (UdsModuleID.UDS_CPLD, UdsModuleID.UDS_CURRENT_SHUNT):
            numBytes = 1
        else:
            numBytes = 2
    elif nodeId in twoByteNodes:
        numBytes = 2

    return numBytes


def UDS_need_secondaryBootloader(client, priv, logger):
    """
    static bool UDS_need_secondaryBootloader(UDS_vars_S *privPtr, UDS_nodeID_t node) 
    """
    returnVal = False

    # for logging
    # Initialize the helper client hooks
    # init_helper_hooks( client );

    if client.node.nodeID == NodeID.UDS_NODE_BMS:
        returnVal = True
    elif client.node.nodeID == NodeID.UDS_NODE_DI:
        # get correct download protocol version

        compAndFwTypeVer = UDS_utility_getCompAndFwType(client)
        if not compAndFwTypeVer:
            return False
        else:
            priv['uds_download_protocol_version'] = compAndFwTypeVer[1]

        if priv['uds_download_protocol_version'] > 4:
            # get pcbid
            DELFINO_PCBID = 15

            # get correct bootloader version
            bootloaderVersionInfo = UDS_utility_getBootloaderVersion(client, priv, logger)

            # assumes v4/5 Bootloader
            pcbID = bootloaderVersionInfo['pcbID']

            # only set flag for older non-Delfino boards
            returnVal = (pcbID < DELFINO_PCBID)
        else:
            returnVal = True
    elif client.node.nodeID == NodeID.UDS_NODE_DIS:
        returnVal = 1

    return returnVal


def UDS_init_privateVariablesForDownload(client, moduleToProgram, uds_download_protocol_version,
                                         flashBootUpdater, changeBootHWID, updaterCPLDDownload, logger):
    """
    bool UDS_init_privateVariablesForDownload (
    UDS_vars_S *privPtr, uint32_t privSize, UDS_nodeID_t node,
    UDS_moduleID_t moduleToProgram, UDS_byte_t uds_download_protocol_version,
    bool flashBootUpdater, bool changeBootHWID, bool updaterCPLDDownload)
    """
    secondaryBootloader = False
    privPtr = {'node': client.node.nodeID, 'shouldCheckCompAndRev': True}

    vendor = client.node.vendorID

    secondaryBootloader = (secondaryBootloader or
                           (vendor == VendorID.UDS_VENDOR_PEKTRON) or
                           (vendor == VendorID.UDS_VENDOR_CONTINENTAL) or
                           (vendor == VendorID.UDS_VENDOR_JLR))

    if not secondaryBootloader:
        secondaryBootloader = secondaryBootloader or UDS_need_secondaryBootloader(client, privPtr, logger)
        secondaryBootloader = secondaryBootloader or (
            NodeID.UDS_NODE_SSD1 <= client.node.nodeID <= NodeID.UDS_NODE_SSD10)
        secondaryBootloader = secondaryBootloader or (
            client.node.nodeID == NodeID.UDS_NODE_SCM or client.node.nodeID == NodeID.UDS_NODE_SCS)
        secondaryBootloader = secondaryBootloader and (
            moduleToProgram == UdsModuleID.UDS_FLASH_APPLICATION or moduleToProgram == UdsModuleID.UDS_FLASH_BOOTLOADER)

    privPtr['loadSecondaryBootloader'] = secondaryBootloader

    privPtr['flashBootUpdater'] = flashBootUpdater
    privPtr['alreadyTalkingToUpdater'] = False  # by default, we do not know if this is true already
    privPtr['moduleToProgram'] = moduleToProgram
    privPtr['updaterCPLDDownload'] = updaterCPLDDownload
    privPtr['dataBytesPerAddress'] = UDS_findDataBytesPerAddress(client.node.nodeID, moduleToProgram)
    privPtr['uds_download_protocol_version'] = uds_download_protocol_version
    privPtr['changeBootloaderHardwareID'] = changeBootHWID

    # Binary download supported nodes
    if IS_BHX_NODE(client.node):
        privPtr['binDownload'] = True

    return privPtr
