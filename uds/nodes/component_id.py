"""
component_id.py
Created on Apr 18, 2016

@author: jpetrie

@description: Components is the definition and container for Known Tesla (and vendor) Component IDs.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.

"""
from enum import IntEnum, unique


@unique
class ComponentID(IntEnum):
    """
    Enum container of Component IDs. See Firmware Repo for more info.
    """
    NONE = 0
    THC = 1
    UI = 2
    BMS = 3
    GTW = 4
    DI = 5
    CHG = 6
    EPBM = 7
    CP = 8
    PM = 9
    VCSEC = 12
    MSM = 13
    CHGS = 14
    DICPLD = 15
    CHGCPLD = 16
    DDM = 17
    PDM = 18
    LFT = 19
    SUN = 20
    BDY = 21
    SEC = 22
    PTC = 23
    IC = 26
    VCLEFT = 35
    VCRIGHT = 36
    BMSCPLD = 39
    EPB = 40
    ESP = 41
    EAS = 42
    TPMS = 43
    DC = 44
    SDM = 45
    OCS = 46
    DSP = 47
    EPAS = 49
    SC = 50
    PTCR = 51
    DCCPLD = 52
    DIS = 53
    LC = 54
    RCCM = 55
    SCCM = 56
    TUNER = 57
    CDFPGA = 58
    HND = 59
    TUNERDSP = 60
    TUNERCAL = 61
    DH = 62
    CHGVI = 63
    CHGPH = 64
    TPMSCAL = 65
    PARK = 66
    BCRDM = 67
    CHADA = 68
    BCFDM = 69
    BCREAR = 70
    TAS = 71
    CMP = 72
    BCCEN = 74
    BCKEY = 75
    TPMS_HARD_CAL = 76
    BCFRONT = 77
    DAS = 78
    HVBS = 79
    CNTUNER = 80
    CNTUNERDSP = 81
    CNTUNERCAL = 82
    CNTUNERDAB = 83
    BBM = 84
    RADFL = 85
    RADFR = 86
    RADC = 87
    RADRL = 88
    RADRR = 89
    PARK2 = 90
    CHGRLY = 91
    RCM = 92
    STPOD = 93
    STTHC = 94
    STDCBC = 95
    BCS2L = 96
    BCS2C = 97
    BCS2R = 98
    SSTHC = 99
    EUTUNER = 100
    EUTUNERDSP = 101
    EUTUNERCAL = 102
    EUTUNERDAB = 103
    JPTUNER = 104
    JPTUNERDSP = 105
    JPTUNERCAL = 106
    JPTUNERDAB = 107
    HKTUNER = 108
    HKTUNERDSP = 109
    HKTUNERCAL = 110
    HKTUNERDAB = 111
    IBOOST = 112
    AUTUNER = 113
    AUTUNERDSP = 114
    AUTUNERCAL = 115
    AUTUNERDAB = 116
    WC = 117
    BCFALCON = 118
    DHPC = 119
    TUNERAUTO = 120
    SNS_CLD1 = 121
    TUNERHD = 122
    TUNERAUTODSP = 123
    SWHTC = 124
    BCFALCD = 125
    MSMD = 126
    GB = 127
    LCC = 128
    RLSCAL = 129
    STINV = 130
    PTCM3 = 131
    VCFRONT = 134,

    TBD = 0xffff

if __name__ == "__main__":
    print __doc__
    print ComponentID.__doc__
