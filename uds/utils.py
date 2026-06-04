"""
Created on Apr 4, 2016

@author: jpetrie

@description: a few module agnostic utilities for the UDS package.

"""

# Extended Python
import math
import ctypes  # it sucks
import binascii

# Tesla Python
from core.udsClient import new_uint8Array
from core.udsClient import uint8Array_getitem
from core.udsClient import uint8Array_setitem

# Constants
NIBBLE = 4
LO_NIB = 0x0F
HI_NIB = 0xF0
MAX_BYTE_LOG = 256  # Woo!
BYTE_ARRAY_LEN = 8  # Standard CAN Frame has 8 bytes.


class BootDataBytes(int):
    """
    For Bytes
    """
    # bytes 1, 2
    ComponentLo = 1
    ComponentHi = 3

    # byte 3
    PCBALo = 3
    PCBAHi = 4

    # byte 4
    AssemblyLo = 4
    AssemblyHi = 5

    # bytes 5, 6
    UsageLo = 5
    UsageHi = 7

    # byte 7 is unused

    # byte 8
    FirmwareTypeLo = 8
    FirmwareTypeHi = 9

    # bytes 9 - 12
    GitHashLo = 9
    GitHashHi = 13

    # bytes 17,18
    ConfigLo = 17
    ConfigHi = 19


class BootDataString(int):
    ComponentLo = 3
    ComponentHi = 7
    PCBALo = 7
    PCBAHi = 9
    AssemblyLo = 9
    AssemblyHi = 11
    UsageLo = 11
    UsageHi = 15
    FirmwareTypeLo = 17
    FirmwareTypeHi = 19
    GitHashLo = 19
    GitHashHi = 35
    ConfigLo = 35
    ConfigHi = 39


def to_byte_array(pyArr):
    """
    to Byte Array converts a python array of ints to a ctypes byte array.
    :param pyArr: <list of int> a python int array
    :return byteArr: <list of c_uint8> a ctypes byte array
    """
    arrLen = len(pyArr)

    byteArr = new_uint8Array(arrLen)  # This really sucks

    if arrLen > 0:
        for num in xrange(0, arrLen):
            uint8Array_setitem(byteArr, num, (pyArr[num]) & 0xff)
    else:
        pass

    return byteArr


def from_byte_array(byteArr, arrLen):
    """
    from Byte Array converts a ctypes byte array into a python list of int.
    :param byteArr: <c_uint8Array> the ctypes byte array
    :param arrLen: <int> the length of the array
    :return pyArr: <list of int> the python array
    """

    if arrLen > 0:
        pyArr = [0] * arrLen
        for num in xrange(0, arrLen):
            pyArr[num] = uint8Array_getitem(byteArr, num) & 0xff
    else:
        pyArr = []

    return pyArr


def from_pcan_byte_array(byteArr, arrLen):
    """
    from PCAN Byte Array converts a PCAN byte array into a python list of int.
    :param byteArr: <c_ubyte_Array_8> the PCAN byte array
    :param arrLen: <int> the length of the array
    :return pyArr: <list of int> the python array
    """
    if arrLen > 0:
        pyArr = [0] * arrLen
        for num in xrange(0, arrLen):
            pyArr[num] = byteArr[num] & 0xff
    else:
        pyArr = []

    return pyArr


def fill_uds_byte_array_with_data(byteArray, data):
    """
    Makes a byte array out of an hex data string.
    :param byteArray: <c_uint8Array> input byte array
    :param data: <string> byte string
    :return byteArray: <c_uint8Array> the output byte array, which is the one you gave us, too.  ctypes sucks.
    """
    index = 0
    for idx, _ in enumerate(byteArray):
        byteArray[idx] = int(data[index:index + 2], 16)
        index += 2

    return byteArray


def double_to_array(double):
    """
    Double to Array takes a 64bit number and packs it into a byte array.  No endianness considerations.
    :param double: <double> a 64bit number.
    :return byteArray: <ctypes.c_ubyte_Array_8> a ctypes array with 8 bytes.
    """
    byteArray = (ctypes.c_uint8 * 8)()

    for index in range(0, BYTE_ARRAY_LEN):
        byteArray[index] = double >> ((BYTE_ARRAY_LEN - 1 - index) * BYTE_ARRAY_LEN)

    return byteArray


def array_to_double(byteArray):
    """
    Array to Double takes a byte array and packs it into a double.  No endianness considerations.
    :param byteArray: <ctypes.c_ubyte_Array_8> a ctypes array with 8 bytes.
    :return double: <double> a 64bit number.
    """
    double = 0x0000000000000000  # whew!

    for index in range(0, 8):
        double |= byteArray[index] << ((BYTE_ARRAY_LEN - 1 - index) * BYTE_ARRAY_LEN)

    return double


def get_address_size_format(address, size):
    """
    Get Address Size Format runs a weird routine that R(W)MBA needs to pack byte sizes into a single byte.
    :param address: <number> the address
    :param size: <number> the size
    :return addressSizeFormat: <number> a single byte formatted as requested.
    """
    # Craft the addressAndSizeFormatter value.  Upper nibble is sizeLen, lower nibble is addressLen
    addressSizeFormat = (int(math.ceil(math.log(address, MAX_BYTE_LOG))) & LO_NIB) | \
                        ((int(math.ceil(math.log(size, MAX_BYTE_LOG))) << NIBBLE) & HI_NIB)

    return addressSizeFormat


def split_boot_info(bootInfo):
    """
    Split Boot Info helps split out the bootloader information.
    :param bootInfo: <hex data string or list of numbers> the raw boot data
    :return splitBoot: <dict> a dictionary with the split boot info.
    """

    if isinstance(bootInfo, basestring):
        # Old school, split by the numbers
        splitBoot = {"ComponentID": int(bootInfo[BootDataString.ComponentLo:BootDataString.ComponentHi], 16),
                     "PCBAID": int(bootInfo[BootDataString.PCBALo:BootDataString.PCBAHi], 16),
                     "AssemblyID": int(bootInfo[BootDataString.AssemblyLo:BootDataString.AssemblyHi], 16),
                     "UsageID": int(bootInfo[BootDataString.UsageLo:BootDataString.UsageHi], 16),
                     "FirmwareType": int(bootInfo[BootDataString.FirmwareTypeLo:BootDataString.FirmwareTypeHi], 16),
                     "GitHash": int(bootInfo[BootDataString.GitHashLo:BootDataString.GitHashHi], 16),
                     "ConfigID": int(bootInfo[BootDataString.ConfigLo:BootDataString.ConfigHi], 16)}
    else:
        byteArray = bytearray(bootInfo)
        splitBoot = {"ComponentID": "0x" + binascii.hexlify(byteArray[BootDataBytes.ComponentLo:
                                                                      BootDataBytes.ComponentHi]).upper(),
                     "PCBAID": "0x" + binascii.hexlify(byteArray[BootDataBytes.PCBALo:BootDataBytes.PCBAHi]).upper(),
                     "AssemblyID": "0x" + binascii.hexlify(byteArray[BootDataBytes.AssemblyLo:
                                                                     BootDataBytes.AssemblyHi]).upper(),
                     "UsageID": "0x" + binascii.hexlify(byteArray[BootDataBytes.UsageLo:BootDataBytes.UsageHi]).upper(),
                     "FirmwareType": "0x" + binascii.hexlify(byteArray[BootDataBytes.FirmwareTypeLo:
                                                                       BootDataBytes.FirmwareTypeHi]).upper(),
                     "GitHash": binascii.hexlify(byteArray[BootDataBytes.GitHashLo:BootDataBytes.GitHashHi]).upper(),
                     "ConfigID": "0x" + binascii.hexlify(byteArray[BootDataBytes.ConfigLo:
                                                                   BootDataBytes.ConfigHi]).upper()}

    return splitBoot


if __name__ == '__main__':
    print __doc__
