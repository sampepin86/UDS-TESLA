"""
boot_id.py
Created on Apr 18, 2016

@author: jpetrie

@description: BootID is the definition and container for Known Tesla (and vendor) Boot CAN IDs.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.

"""
from enum import IntEnum


# noinspection PyPep8
class BootID(IntEnum):
    """
    The CAN IDs of the boot ID message
    """
    NONE_BOOT_MID = 0
    BDY_BCCEN_BOOTID_MID       = 0x521    # BCCEN_bootID
    BDY_BCREAR_BOOTID_MID      = 0x522    # BCREAR_bootID
    BDY_BCFRONT_BOOTID_MID     = 0x523    # BCFRONT_bootID
    BDY_BCFDM_BOOTID_MID       = 0x524    # BCFDM_bootID
    BDY_BCFPM_BOOTID_MID       = 0x525    # BCFPM_bootID
    BDY_BCRDM_BOOTID_MID       = 0x526    # BCRDM_bootID
    BDY_BCRPM_BOOTID_MID       = 0x527    # BCRPM_bootID
    BDY_SNSCLL_BOOTID_MID      = 0x528    # SNSCLL_bootID
    BDY_BCFALC_BOOTID_MID      = 0x529    # BCFALC_bootID
    BDY_BCFALCD_BOOTID_MID     = 0x52E
    BDY_BCFALCP_BOOTID_MID     = 0x52A
    BDY_BCS2L_BOOTID_MID       = 0x52B    # BCS2L_bootID
    BDY_BCS2C_BOOTID_MID       = 0x52C    # BCS2C_bootID
    BDY_BCS2R_BOOTID_MID       = 0x52D    # BCS2R_bootID
    BDY_SNSCUR_BOOTID_MID      = 0x52F    # SNSCUR_bootID
    TH_PTCR_BOOTID_MID         = 0x515    # PTCR_bootID
    BFT_MSMP_BOOTID_MID        = 0x5FB    # MSMP_bootID
    TH_CMP_BOOTID_MID          = 0x633    # CMP_bootID
    BFT_PTC_BOOTID_MID         = 0x516    # PTC_bootID
    BFT_RCCM_BOOTID_MID        = 0x517    # RCCM_bootID
    BFT_MSM_BOOTID_MID         = 0x5FC    # MSM_bootID
    PT_CHADA_BootID_MID        = 0x62F    # chademo bootID
    PT_PMS_BOOTID_MID          = 0x5E4    # PMS_bootID
    PT_CHGPH1_BOOTID_MID       = 0x5E7    # CHGPH1_bootID
    PT_CHGPH2_BOOTID_MID       = 0x5E9    # CHGPH2_bootID
    PT_CHGPH3_BOOTID_MID       = 0x5EB    # CHGPH3_bootID
    PT_CHG_BOOTID_MID          = 0x5EC    # CHG_bootID
    PT_CHGRLY_BOOTID_MID       = 0x5EE    # CHGRLY_bootID
    PT_BMS_BOOTID_MID          = 0x5F2    # BMS_bootID
    PT_PM_BOOTID_MID           = 0x5F4    # PM_bootID
    PT_DIS_BOOTID_MID          = 0x5F5    # DIS_bootID
    PT_DI_BOOTID_MID           = 0x5F6    # DI_bootID
    PT_CHGS_BOOTID_MID         = 0x5FC    # CHGS_bootID
    PT_CP_BOOTID_MID           = 0x5FE    # CP_bootID
    PT_CMP_BOOTID_MID          = 0x633    # CMP_bootID
    PT_THC_BOOTID_MID          = 0x63A    # THC_bootID
    PT_DCDC_BOOTID_MID         = 0x620    # DCDC_bootID
    PT_CHGSPH1_BOOTID_MID      = 0x667    # CHGSPH1_bootID
    PT_CHGSPH2_BOOTID_MID      = 0x669    # CHGSPH2_bootID
    PT_CHGSPH3_BOOTID_MID      = 0x66B    # CHGSPH3_bootID
    CH_EPB_BOOTID_MID          = 0x5F4    # EPB_bootID
    CH_EPBM_BOOTID_MID         = 0x5F7    # EPBM_bootID
    CH_IC_BOOTID_MID           = 0x5FC    # IC_bootID
    CH_TPMS_BOOTID_MID         = 0x5FF    # TPMS_bootID
    CH_DAS_BOOTID_MID          = 0x639    # DAS_bootID
    CH_ESP_BOOTID_MID          = 0x646    # ESP_bootID
    CH_IBST_BOOTID_MID         = 0x66D    # IBST_bootID
    CH_TAS_BOOTID_MID          = 0x521    # TAS_bootID is EAS_bootID
    PT_BMS01_BOOTID_MID        = 0x5F1    # BMS01_bootID
    PT_BMS02_BOOTID_MID        = 0x5F2    # BMS02_bootID
    PT_BMS03_BOOTID_MID        = 0x5F3    # BMS03_bootID
    PT_BMS04_BOOTID_MID        = 0x5F4    # BMS04_bootID
    PT_BMS05_BOOTID_MID        = 0x5F5    # BMS05_bootID
    PT_BMS06_BOOTID_MID        = 0x5F6    # BMS06_bootID
    PT_BMS07_BOOTID_MID        = 0x5F7    # BMS07_bootID
    PT_BMS08_BOOTID_MID        = 0x5F8    # BMS08_bootID
    PT_BMS09_BOOTID_MID        = 0x5F9    # BMS09_bootID
    PT_BMS10_BOOTID_MID        = 0x5FA    # BMS10_bootID
    PT_CHG01PH1_BOOTID_MID     = 0x581    # CHG01PH1_bootID
    PT_CHG02PH1_BOOTID_MID     = 0x582    # CHG02PH1_bootID
    PT_CHG03PH1_BOOTID_MID     = 0x583    # CHG03PH1_bootID
    PT_CHG04PH1_BOOTID_MID     = 0x584    # CHG04PH1_bootID
    PT_CHG05PH1_BOOTID_MID     = 0x585    # CHG05PH1_bootID
    PT_CHG06PH1_BOOTID_MID     = 0x586    # CHG06PH1_bootID
    PT_CHG07PH1_BOOTID_MID     = 0x587    # CHG07PH1_bootID
    PT_CHG08PH1_BOOTID_MID     = 0x588    # CHG08PH1_bootID
    PT_CHG09PH1_BOOTID_MID     = 0x589    # CHG09PH1_bootID
    PT_CHG10PH1_BOOTID_MID     = 0x58A    # CHG10PH1_bootID
    PT_CHG11PH1_BOOTID_MID     = 0x58B    # CHG11PH1_bootID
    PT_CHG12PH1_BOOTID_MID     = 0x58C    # CHG12PH1_bootID
    PT_CHG01PH2_BOOTID_MID     = 0x591    # CHG01PH2_bootID
    PT_CHG02PH2_BOOTID_MID     = 0x592    # CHG02PH2_bootID
    PT_CHG03PH2_BOOTID_MID     = 0x593    # CHG03PH2_bootID
    PT_CHG04PH2_BOOTID_MID     = 0x594    # CHG04PH2_bootID
    PT_CHG05PH2_BOOTID_MID     = 0x595    # CHG05PH2_bootID
    PT_CHG06PH2_BOOTID_MID     = 0x596    # CHG06PH2_bootID
    PT_CHG07PH2_BOOTID_MID     = 0x597    # CHG07PH2_bootID
    PT_CHG08PH2_BOOTID_MID     = 0x598    # CHG08PH2_bootID
    PT_CHG09PH2_BOOTID_MID     = 0x599    # CHG09PH2_bootID
    PT_CHG10PH2_BOOTID_MID     = 0x59A    # CHG10PH2_bootID
    PT_CHG11PH2_BOOTID_MID     = 0x59B    # CHG11PH2_bootID
    PT_CHG12PH2_BOOTID_MID     = 0x59C    # CHG12PH2_bootID
    PT_CHG01PH3_BOOTID_MID     = 0x5A1    # CHG01PH3_bootID
    PT_CHG02PH3_BOOTID_MID     = 0x5A2    # CHG02PH3_bootID
    PT_CHG03PH3_BOOTID_MID     = 0x5A3    # CHG03PH3_bootID
    PT_CHG04PH3_BOOTID_MID     = 0x5A4    # CHG04PH3_bootID
    PT_CHG05PH3_BOOTID_MID     = 0x5A5    # CHG05PH3_bootID
    PT_CHG06PH3_BOOTID_MID     = 0x5A6    # CHG06PH3_bootID
    PT_CHG07PH3_BOOTID_MID     = 0x5A7    # CHG07PH3_bootID
    PT_CHG08PH3_BOOTID_MID     = 0x5A8    # CHG08PH3_bootID
    PT_CHG09PH3_BOOTID_MID     = 0x5A9    # CHG09PH3_bootID
    PT_CHG10PH3_BOOTID_MID     = 0x5AA    # CHG10PH3_bootID
    PT_CHG11PH3_BOOTID_MID     = 0x5AB    # CHG11PH3_bootID
    PT_CHG12PH3_BOOTID_MID     = 0x5AC    # CHG12PH3_bootID
    PT_CHG01_BOOTID_MID        = 0x5E1    # CHG01_bootID
    PT_CHG02_BOOTID_MID        = 0x5E2    # CHG02_bootID
    PT_CHG03_BOOTID_MID        = 0x5E3    # CHG03_bootID
    PT_CHG04_BOOTID_MID        = 0x5E4    # CHG04_bootID
    PT_CHG05_BOOTID_MID        = 0x5E5    # CHG05_bootID
    PT_CHG06_BOOTID_MID        = 0x5E6    # CHG06_bootID
    PT_CHG07_BOOTID_MID        = 0x5E7    # CHG07_bootID
    PT_CHG08_BOOTID_MID        = 0x5E8    # CHG08_bootID
    PT_CHG09_BOOTID_MID        = 0x5E9    # CHG09_bootID
    PT_CHG10_BOOTID_MID        = 0x5EA    # CHG10_bootID
    PT_CHG11_BOOTID_MID        = 0x5EB    # CHG11_bootID
    # PT_CHG12_BOOTID_MID        = 0x5EC    # CHG12_bootID
    PT_SCS_BOOTID_MID          = 0x5FE    # SCS_bootID
    PT_SCM_BOOTID_MID          = 0x5FF    # SCM_bootID
    PT_CHGVI_BOOTID_MID        = 0x5EC
    VC_VCFRONT_BOOTID_MID = 0x501
    VC_VCLEFT_BOOTID_MID  = 0x502
    VC_VCRIGHT_BOOTID_MID = 0x503
    VC_VCSEC_BOOTID_MID   = 0x519
    VC_EPBL_BOOTID_MID    = 0x533
    VC_EBPR_BOOTID_MID    = 0x532

if __name__ == "__main__":
    print __doc__
    print BootID.__doc__
