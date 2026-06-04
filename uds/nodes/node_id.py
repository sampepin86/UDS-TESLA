"""
node_id.py
Created on Apr 18, 2016

@author: jpetrie

@description: NodeID is the definition and container for Known Tesla (and vendor) UDS Node IDs.
    Related to the node order in FW Download Tool. Not sure how it is to be used now.  Maybe not needed.
    This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
    must match. It provides an easy/separate interface for development.

"""
from enum import Enum, unique


class AutoNumber(Enum):
    """
    Shamelessly stolen from https://docs.python.org/3/library/enum.html#autonumber
    but modified to accept a specified value
    """

    def __new__(cls, *args, **kwargs):
        value = len(cls.__members__) if len(args) == 0 else args[0]
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __int__(self):
        # Returns the automatically-generated unique node ID number for the specified Node
        return self._value_

    def __cmp__(self, other):
        return cmp(self.value, other.value)

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value


@unique
class NodeID(AutoNumber):
    """
    The Node ID the value of these is unimportant
    """
    UDS_NODE_NONE = 0  # used for range checking
    UDS_NODE_BCCEN = ()
    UDS_NODE_BCFALC = ()
    UDS_NODE_BCFALCD = ()  # ?
    UDS_NODE_BCFALCP = ()  # ?
    UDS_NODE_BCFDM = ()
    UDS_NODE_BCFPM = ()
    UDS_NODE_BCFRONT = ()
    UDS_NODE_BCRDM = ()
    UDS_NODE_BCREAR = ()
    UDS_NODE_BCRPM = ()
    UDS_NODE_BCS2L = ()
    UDS_NODE_BCS2C = ()
    UDS_NODE_BCS2R = ()
    UDS_NODE_BDY = ()
    UDS_NODE_BMS = ()
    UDS_NODE_CHADA = ()
    UDS_NODE_GB = ()
    UDS_NODE_CHG = ()
    UDS_NODE_CHGS = ()
    UDS_NODE_VCFRONT = ()
    UDS_NODE_VCLEFT = ()
    UDS_NODE_VCRIGHT = ()
    UDS_NODE_VCSEC = ()
    UDS_NODE_EPBL = ()
    UDS_NODE_EPBR = ()
    # Supercharger Gen II Phase Nodes start 
    UDS_NODE_CHG01PH1 = ()
    UDS_NODE_CHG02PH1 = ()
    UDS_NODE_CHG03PH1 = ()
    UDS_NODE_CHG04PH1 = ()
    UDS_NODE_CHG05PH1 = ()
    UDS_NODE_CHG06PH1 = ()
    UDS_NODE_CHG07PH1 = ()
    UDS_NODE_CHG08PH1 = ()
    UDS_NODE_CHG09PH1 = ()
    UDS_NODE_CHG10PH1 = ()
    UDS_NODE_CHG11PH1 = ()
    UDS_NODE_CHG12PH1 = ()
    UDS_NODE_CHG01PH2 = ()
    UDS_NODE_CHG02PH2 = ()
    UDS_NODE_CHG03PH2 = ()
    UDS_NODE_CHG04PH2 = ()
    UDS_NODE_CHG05PH2 = ()
    UDS_NODE_CHG06PH2 = ()
    UDS_NODE_CHG07PH2 = ()
    UDS_NODE_CHG08PH2 = ()
    UDS_NODE_CHG09PH2 = ()
    UDS_NODE_CHG10PH2 = ()
    UDS_NODE_CHG11PH2 = ()
    UDS_NODE_CHG12PH2 = ()
    UDS_NODE_CHG01PH3 = ()
    UDS_NODE_CHG02PH3 = ()
    UDS_NODE_CHG03PH3 = ()
    UDS_NODE_CHG04PH3 = ()
    UDS_NODE_CHG05PH3 = ()
    UDS_NODE_CHG06PH3 = ()
    UDS_NODE_CHG07PH3 = ()
    UDS_NODE_CHG08PH3 = ()
    UDS_NODE_CHG09PH3 = ()
    UDS_NODE_CHG10PH3 = ()
    UDS_NODE_CHG11PH3 = ()
    UDS_NODE_CHG12PH3 = ()
    # Supercharger Gen II Phase Nodes end
    UDS_NODE_CHGPH1 = ()
    UDS_NODE_CHGPH2 = ()
    UDS_NODE_CHGPH3 = ()
    UDS_NODE_CHGSPH1 = ()
    UDS_NODE_CHGSPH2 = ()
    UDS_NODE_CHGSPH3 = ()
    UDS_NODE_CHGRLY = ()
    # Supercharger Gen II VI Nodes start 
    UDS_NODE_CHG01VI = ()
    UDS_NODE_CHG02VI = ()
    UDS_NODE_CHG03VI = ()
    UDS_NODE_CHG04VI = ()
    UDS_NODE_CHG05VI = ()
    UDS_NODE_CHG06VI = ()
    UDS_NODE_CHG07VI = ()
    UDS_NODE_CHG08VI = ()
    UDS_NODE_CHG09VI = ()
    UDS_NODE_CHG10VI = ()
    UDS_NODE_CHG11VI = ()
    UDS_NODE_CHG12VI = ()
    # Supercharger Gen II VI Nodes end 
    UDS_NODE_CHGVI = ()
    UDS_NODE_CHGSVI = ()
    UDS_NODE_CMP = ()
    UDS_NODE_CP = ()
    UDS_NODE_CTPMS = ()
    UDS_NODE_DAS = ()
    UDS_NODE_DCDC = ()
    UDS_NODE_DDM = ()
    UDS_NODE_DHFD = ()
    UDS_NODE_DHFP = ()
    UDS_NODE_DHRD = ()
    UDS_NODE_DHRP = ()
    UDS_NODE_DI = ()
    UDS_NODE_DIS = ()
    UDS_NODE_EAS = ()
    UDS_NODE_EPAS = ()
    UDS_NODE_EPAS2 = ()
    UDS_NODE_EPB = ()
    UDS_NODE_EPBM = ()
    UDS_NODE_ESP = ()
    UDS_NODE_ESPCAL = ()
    UDS_NODE_ESP2 = ()
    UDS_NODE_GW = ()
    UDS_NODE_HNDFD = ()
    UDS_NODE_HNDFP = ()
    UDS_NODE_HNDRD = ()
    UDS_NODE_HNDRP = ()
    UDS_NODE_HVBS = ()
    UDS_NODE_IBST = ()
    UDS_NODE_IBSTCAL = ()
    UDS_NODE_IC = ()
    UDS_NODE_LFT = ()
    UDS_NODE_LM = ()
    UDS_NODE_LS = ()
    UDS_NODE_MSM = ()
    UDS_NODE_MSMP = ()
    UDS_NODE_MSMD = ()
    UDS_NODE_OCS = ()
    UDS_NODE_PARK = ()
    UDS_NODE_PARK2 = ()
    UDS_NODE_PDM = ()
    UDS_NODE_PM = ()
    UDS_NODE_PMS = ()
    UDS_NODE_PTC = ()
    UDS_NODE_PTCR = ()
    UDS_NODE_RADC = ()
    UDS_NODE_RADRL = ()
    UDS_NODE_RADRR = ()
    UDS_NODE_RCM = ()
    UDS_NODE_RCCM = ()
    UDS_NODE_RLSCAL = ()
    UDS_NODE_SC1 = ()
    UDS_NODE_SC2 = ()
    UDS_NODE_SC3 = ()
    UDS_NODE_SC4 = ()
    UDS_NODE_SC5 = ()
    UDS_NODE_SC6 = ()
    UDS_NODE_SC7 = ()
    UDS_NODE_SC8 = ()
    UDS_NODE_SC9 = ()
    UDS_NODE_SC10 = ()
    UDS_NODE_SC11 = ()
    UDS_NODE_SC12 = ()
    UDS_NODE_SCCM = ()
    UDS_NODE_SCM = ()
    UDS_NODE_SCS = ()
    UDS_NODE_SDM = ()
    UDS_NODE_SEC = ()
    UDS_NODE_SNSCLL1 = ()
    UDS_NODE_SNSCLR1 = ()
    UDS_NODE_SNSCUL1 = ()
    UDS_NODE_SNSCUR1 = ()
    UDS_NODE_SSD1 = ()
    UDS_NODE_SSD2 = ()
    UDS_NODE_SSD3 = ()
    UDS_NODE_SSD4 = ()
    UDS_NODE_SSD5 = ()
    UDS_NODE_SSD6 = ()
    UDS_NODE_SSD7 = ()
    UDS_NODE_SSD8 = ()
    UDS_NODE_SSD9 = ()
    UDS_NODE_SSD10 = ()
    UDS_NODE_SUN = ()
    UDS_NODE_TAS = ()
    UDS_NODE_THC = ()
    UDS_NODE_TPMS = ()
    UDS_NODE_TUNER = ()
    UDS_NODE_WC = ()
    UDS_NODE_LAST = ()  # used for range checking


if __name__ == "__main__":
    print __doc__
    print NodeID.__doc__
