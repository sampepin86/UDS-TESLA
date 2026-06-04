from uds.sequences.utils import UDS_utility_getBootloaderVersion, UDS_utility_talkToBootloader
from uds.typedefs import UdsSessionType
from tesla_v3_enter_bootloader import tesla_v3_enterBootloader


def UDS_Operation_prepareTeslaECU(client, priv, logger):
    """
    shamelessly stolen from:
    https://stash.teslamotors.com/projects/TBX/repos/lib-vehicle/commits/625c9ca943c8870b1351e985284c7939098e1ae5#cpp/Uds/client/UDS_Download_Operations.c

    ensures the ECU is in the correct state for... whatever comes next and returns the bootloader version

    bool UDS_Operation_prepareTeslaECU(UDS_vars_S *privPtr, UDS_bootloaderVersionInfo_t *bootloaderVersionInfoPtr)
    :param client:  UDS.client
    :param priv: <dict> containing "useful" information for communicating w/ the ECUs
    :param logger: logger object
    :return: bootloaderVersion | <dict> containing a githash or svn commit id if successful, or
                                        an empty dictionary if we can continue w/o the bootloader version(?) or
                                        None if we could not prepare the ECU
    """

    bootloaderVersion = None
    if tesla_v3_enterBootloader(client, logger) \
       and client.diagnostic_session(UdsSessionType.PROGRAMMING_SESSION, True) == 0 \
       and UDS_utility_talkToBootloader(client, logger):
        if priv['flashBootUpdater'] and priv['alreadyTalkingToUpdater']:
            bootloaderVersion = {}
        else:
            # get bootloader version info but no hwid
            bootloaderVersion = UDS_utility_getBootloaderVersion(client, priv, logger)

    return bootloaderVersion
