"""
Created on Fri Jan 24 18:37:58 2014

View readme for more information.

@author: Spencer Hawkins <shawkins@teslamotors.com>
@author(edited): Ben Drobiz <bdrobiz@teslamotors.com>
conformed the functions to accept new uds command protocol
@author(edited): jpetrie 3/16/16 - revamp
"""

# Base Python
import logging
import sys
import threading
import os
import time

# Tesla Python
import uds.utils as utils
import uds.nodes as nodes
import uds.constants as constants
from uds.typedefs import UdsResetType, UdsModuleID, UdsSessionType
from uds import TeslaUtilities


class BootIDMessageUnknownError(Exception):
    pass


class DownloadException(Exception):
    pass


def uds_bootloader_download(client, filename, logger=None):
    """
    Downloads a bootloader module
    :param client: <UDS.client.Client> instance
    :param filename: <string> full path to the file to download.
    :param logger: logger object, or false to not log
    :return error_code: <number> the resultant error code.
    """
    return uds_download(client, filename, download_type=UdsModuleID.UDS_FLASH_BOOTLOADER, logger=logger)

def uds_cpld_download(client, filename, logger=None):
    """
    Downloads a CPLD module
    :param client: <UDS.client.Client> instance
    :param filename: <string> full path to the file to download.
    :param logger: logger object, or false to not log
    :return error_code: <number> the resultant error code.
    """
    return uds_download(client, filename, download_type=UdsModuleID.UDS_CPLD, logger=logger)

def uds_download(client, filename, download_type=UdsModuleID.UDS_FLASH_APPLICATION, logger=None):
    """
    UDS Download initiates a UDS download
    :param client: <UDS.client.Client> instance
    :param filename: <string> full path to the file to download.
    :param download_type: <number> Look under Constants.py
    :param logger: logger object, or false to not log
    :return error_code: <number> the resultant error code.
    """

    # make a logger if we didn't get one
    if logger is None:
        logger = TeslaUtilities.get_logger()
    elif not logger:
        logger = TeslaUtilities.get_logger(logging.ERROR)

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
        logger.info("Downloading file to ECU: {0}.".format(filename))

        if not os.path.isfile(filename):
            msg = "Could not open supplied file: {0}.".format(filename)
            logger.error(msg)
            raise IOError(msg)

        # Let the ECU know we are here!
        time.sleep(constants.MAGIC_DOWNLOAD_WAIT)

        # read 101 to see what is currently running on the controller
        err, data = client.read_data(0x0101, constants.ID_LENGTHS[0x101])  # Magic numbers! -JP

        if err & 0xFF00 == 0x100 and err & 0xFF in (constants.SERVICE_NOT_SUPPORTED,
                                                    constants.SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION):
            # Service not supported error, assume we are talking with the application
            logger.info("Read 0x101: Service not supported")
            talking_with = constants.APPLICATION_TALKING
        elif err & 0xFF00 == 0x000 and err == constants.CAN_UNEXP_PDU_01:
            # This error is normally thrown when the ECU didn't respond
            msg = "ECU didn't respond! Is it turned on?"
            logger.error(msg)
            raise DownloadException(msg)
        else:
            talking_with = data[1]  # Magic Number! This time my fault - JP

        if talking_with == constants.APPLICATION_TALKING:
            logger.info("Talking to Application.")

        elif talking_with == constants.BOOTLOADER_TALKING:
            logger.info("Talking with Bootloader.")

        elif talking_with == constants.UPDATER_TALKING:
            logger.info("Talking to Updater.")

        if download_type == UdsModuleID.UDS_FLASH_BOOTLOADER and talking_with != constants.UPDATER_TALKING:
            msg = "Need to talk to Updater for a Bootloader Update."
            logger.error(msg)
            raise DownloadException(msg)


        # TODO: Clean up these conditionals and get a more robust bootloader entry routine.
        if download_type == UdsModuleID.UDS_FLASH_APPLICATION or download_type == UdsModuleID.UDS_CPLD:
            if talking_with != constants.BOOTLOADER_TALKING:
                # not talking to bootloader continue to tp and do reset
                client.ecu_reset(UdsResetType.HARD_RESET, False)
                time.sleep(2)

            if client.node in [nodes.CP, nodes.CHGPH1, nodes.CHGPH2, nodes.CHGPH3]:
                _ = client.diagnostic_session(UdsSessionType.PROGRAMMING_SESSION, True)

            error_code, data = client.read_data(0x0101, constants.ID_LENGTHS[0x101])  # Magic Numbers! -JP

            if error_code:
                msg = "Could not read data ID 0x101 from ECU."
                logger.error(msg)
                abort_tp_thread = True
                raise DownloadException(msg)
            else:
                talking_with = data[1]  # Magic Number! This time my fault - JP

                if talking_with == constants.APPLICATION_TALKING:
                    msg = "Talking to Application, need to be talking to Bootloader."
                    logger.error(msg)
                    abort_tp_thread = True
                    raise DownloadException(msg)

                elif talking_with == constants.UPDATER_TALKING:
                    msg = "Talking to Updater, need to be talking to Bootloader."
                    logger.error(msg)
                    abort_tp_thread = True
                    raise DownloadException(msg)

        # Put the board in programming mode
        dsc_result = client.diagnostic_session(UdsSessionType.PROGRAMMING_SESSION, True)

        if dsc_result != 0:
            msg = "Error during Diagnostic Session, return code {0}.".format(dsc_result)
            logger.error(msg)
            raise ValueError(msg)

        abort_tp_thread = True
        # After Tester Present stops, board should boot.
        if not client.wait_for_boot_id(True):
            msg = "Couldn't get a Boot ID."
            logger.error(msg)
            raise DownloadException(msg)

        # Get Security Access
        sa_result = client.security_access(5)

        if sa_result == 0:
            logger.info("Getting Security Access... Success.")
        else:
            msg = "Error during Security Access, return code {0}.".format(sa_result)
            logger.error(msg)
            raise ValueError(msg)

        # Get info about the Bootloader
        logger.info("Module Info")
        _unused_err, boot_info = client.read_data(0xF180, constants.ID_LENGTHS[0xF180])

        boot_info_split = utils.split_boot_info(boot_info)
        stars = "***********************************************"
        logger.info(stars)
        logger.info("Bootloader hardware ID signature:")
        logger.info("    Component ID: {0}".format(boot_info_split["ComponentID"]))
        logger.info("    PCBA ID: {0}".format(boot_info_split["PCBAID"]))
        logger.info("    Assembly ID: {0}".format(boot_info_split["AssemblyID"]))
        logger.info("    Usage ID: {0}".format(boot_info_split["UsageID"]))
        logger.info("    Firmware Type: {0}".format(boot_info_split["FirmwareType"]))
        logger.info("    Git Hash: {0}".format(boot_info_split["GitHash"]))
        logger.info("    Config ID: {0}".format(boot_info_split["ConfigID"]))
        logger.info(stars)

        # Write Download Type to ECU
        wdbi_data = [download_type]
        wdbi_result = client.write_data(0x0102, wdbi_data)

        if wdbi_result != 0:
            msg = "Error during Write Data, return code {0}.".format(wdbi_result)
            logger.error(msg)
            raise ValueError(msg)

        # Erasing all the existing code takes a while sometimes. Increase the timeout while waiting for this routine.
        client.transport.set_read_timeout(15)

        # Send Download Routine
        error_code, rc_result = client.routine_control(0xff00, 1, None, 1)

        # Then set it back
        client.transport.set_read_timeout(3)

        if error_code != 0:
            msg = "Error during routine control 0xFF00, error code {0}.".format(error_code)
            logger.error(msg)
            raise ValueError(msg)

        if rc_result[0] != 0:
            msg = "Error during routine control 0xFF00, return code {0}. Cannot Continue Download.".format(rc_result)
            logger.error(msg)
            raise ValueError(msg)

        regions = client.parse_data_get_size(filename, download_type)

        if download_type not in [UdsModuleID.UDS_CPLD, UdsModuleID.UDS_CURRENT_SHUNT]:
            download_mau = client.node.mau
        else:
            download_mau = 1

        total_size = sum([s for (_, s) in regions])
        total_bytes_left = total_size

        logger.info("Starting download.")
        tic = time.time()

        for start_address, region_size in regions:
            memory_size = 0x3e0  # TODO: Figure out why
            memory_address = start_address / download_mau
            bytes_left = region_size

            # ignore bootloader addresses
            if memory_address == constants.TESLA_TI_BEGIN_FLASH_ADDRESS:
                continue

            while bytes_left > 0:
                calc_percent = (1.0 - (float(total_bytes_left) / float(total_size))) * 100.0

                if calc_percent < 0:
                    calc_percent = 0

                logger.info("{0:.2f}".format(calc_percent))

                if bytes_left < memory_size:
                    memory_size = bytes_left

                error_code, transaction_size = client.request_download_init(memory_address, memory_size)

                if error_code != 0:
                    msg = "Error during Request Download Init, return code {0}.".format(error_code)
                    logger.error(msg)
                    raise ValueError(msg)

                status = client.transfer_data(memory_address, transaction_size, memory_size, download_mau)

                if status != 0:
                    msg = "Error during Transfer Data, return code {0}.".format(status)
                    logger.error(msg)
                    raise ValueError(msg)

                bytes_left -= memory_size
                memory_address += (memory_size / download_mau)
                total_bytes_left -= memory_size

                status = client.request_transfer_exit()

                if status != 0:
                    msg = "Error during Request Transfer Exit, return code {0}.".format(status)
                    logger.error(msg)
                    raise ValueError(msg)

        toc = time.time()
        logger.info("Download finished.")
        logger.info("Download time = {0:0.2f} s.".format((toc - tic)))

        error_code, rc_result = client.routine_control(0x0201, 1, None, 1)

        logger.info("Routine Control 0x0201 = {0}, {1}.".format(error_code, rc_result))

        if error_code != 0:
            msg = "Error during routine_control 0x201, routine error {0}.".format(error_code)
            logger.error(msg)
            raise ValueError(msg)

        if rc_result[0] != 0:
            msg = "Error during routine_control 0x201, return code {0}. Cannot Continue Download.".format(rc_result)
            logger.error(msg)
            raise ValueError(msg)

        error_code, rc_result = client.routine_control(0x0202, 1, None, 1)

        logger.info("Routine Control 0x0202 = {0}, {1}.".format(error_code, rc_result))

        if error_code != 0:
            msg = "Error during routine_control 0x202, routine error {0}.".format(error_code)
            logger.error(msg)
            raise ValueError(msg)

        if rc_result[0] != 0:
            msg = "Error during routine_control 0x202, return code {0}.".format(rc_result)
            logger.error(msg)
            raise ValueError(msg)

        return error_code
    finally:
        abort_tp_thread = True
        tp_thread.join()


if __name__ == "__main__":
    print __doc__
    print uds_download.__doc__

