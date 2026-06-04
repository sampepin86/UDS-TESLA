from enum import IntEnum, unique
import uds.core.udsClient as udsClient


@unique
class UdsRoutineControlType(IntEnum):
    START_ROUTINE = 0x01
    STOP_ROUTINE = 0x02
    REQUEST_ROUTINE_RESULTS = 0x03


@unique
class UdsIoControlType(IntEnum):
    IO_RETURN_TO_ECU = udsClient.returnControlToECU         # 0x01
    IO_RESET_TO_DEFAULT = udsClient.resetToDefault          # 0x02
    IO_FREEZE = udsClient.freezeCurrentState                # 0x03
    IO_SHORT_TERM_ADJUST = udsClient.shortTermAdjustment    # 0x04


@unique
class UdsResetType(IntEnum):
    HARD_RESET = udsClient.hardReset            # 0x01 - watchdog reset - cycles power on-off and resets the peripherals
    KEY_OFF_ON_RESET = udsClient.keyOffOnReset  # 0x02 - same for our purposes
    SOFT_RESET = udsClient.softReset            # 0x03 - Jumps to the begin flash section.


# Diagnostic Session Control type
@unique
class UdsSessionType(IntEnum):
    DEFAULT_SESSION = udsClient.defaultSession                                  # 0x01
    PROGRAMMING_SESSION = udsClient.programmingSession                          # 0x02
    EXTENDED_DIAGNOSTIC_SESSION = udsClient.extendedDiagnosticSession           # 0x03
    SAFETY_SYSTEM_DIAGNOSTIC_SESSION = udsClient.safetySystemDiagnosticSession  # 0x04


@unique
class UdsModuleID(IntEnum):
    UDS_FLASH_APPLICATION = 0  # only bootloader knows how to write here
    UDS_CPLD = 1
    UDS_CURRENT_SHUNT = 2
    UDS_SERIALIZED_BMB = 3
    UDS_LOAD_FLASH_API = 4
    UDS_FLASH_BOOTLOADER = 5  # only bootloader updater knows how to write
    UDS_SECONDARY_APPLICATION = 6
    UDS_CALIBRATION_DATA = 7
    UDS_TERTIARY_APPLICATION = 8
    UDS_SERIALIZED_BMB_BOOTUPDATE = 9
    UDS_ECU_CONFIG = 10
    UDS_SUBCOMPONENT1_BOOT = 11
    UDS_SUBCOMPONENT2_APP = 12
    UDS_SUBCOMPONENT3_FFS = 13  # The SPI based subcomponent app download through ECU app
    UDS_SECONDARY_FLASH_APPLICATION = 14
    # It serves a backup application and is stored at different flash address space.
    UDS_RAM_APPLICATION = 15
    UDS_FLASH_BOOTUPDATER = 16
    UDS_QUATERNARY_APPLICATION = 17
    UDS_INVALID_MODULE = 255
