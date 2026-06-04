"""
resp_id.py
Created on Apr 18, 2016

@author: jpetrie

@description: RespID is the definition and container for Known Tesla (and vendor) UDS Response CAN IDs.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.

"""
from enum import IntEnum


# noinspection PyPep8
class RespID(IntEnum):
    """
    CAN IDs of response message
    """
    UDS_NONE_MID                = 0x000    # NONE/Bounds checking
    UDS_LMRESPONSE_MID          = 0x001    # LM_usdResponse
    UDS_LSRESPONSE_MID          = 0x002    # LS_usdResponse
    BDY_BCCEN_UDSRESPONSE_MID   = 0x691    # BCCEN_udsResponse
    BDY_BCREAR_UDSRESPONSE_MID  = 0x6B2    # BCREAR_udsResponse
    BDY_BCFRONT_UDSRESPONSE_MID = 0x6B3    # BCFRONT_udsResponse
    BDY_BCFDM_UDSRESPONSE_MID   = 0x6B4    # BCFDM_udsResponse
    BDY_BCFPM_UDSRESPONSE_MID   = 0x6B5    # BCFPM_udsResponse
    BDY_BCRDM_UDSRESPONSE_MID   = 0x6B6    # BCRDM_udsResponse
    BDY_BCRPM_UDSRESPONSE_MID   = 0x6B7    # BCRPM_udsResponse
    BDY_BCFALC_UDSRESPONSE_MID  = 0x6B9    # BCFALC_udsResponse
    BDY_BCFALCD_UDSRESPONSE_MID  = 0x6BE   # BCFALCD_udsResponse
    BDY_BCFALCP_UDSRESPONSE_MID  = 0x6BA   # BCFALCP_udsResponse
    BDY_BCS2L_UDSRESPONSE_MID   = 0x6BB    # BCS2L_udsResponse
    BDY_BCS2C_UDSRESPONSE_MID   = 0x6BC    # BCS2C_udsResponse
    BDY_BCS2R_UDSRESPONSE_MID   = 0x6BD    # BCS2R_udsResponse
    BDY_DHFP_UDSRESPONSE_MID    = 0x139    # DHFP_udsResponse
    BDY_DHRP_UDSRESPONSE_MID    = 0x139    # DHRP_udsResponse
    BDY_DHFD_UDSRESPONSE_MID    = 0x13a    # DHFD_udsResponse
    BDY_DHRD_UDSRESPONSE_MID    = 0x13a    # DHRD_udsResponse
    BDY_HNDFP_UDSRESPONSE_MID   = 0x139    # HNDFP_udsResponse
    BDY_HNDRP_UDSRESPONSE_MID   = 0x139    # HNDRP_udsResponse
    BDY_HNDFD_UDSRESPONSE_MID   = 0x13a    # HNDFD_udsResponse
    BDY_HNDRD_UDSRESPONSE_MID   = 0x13a    # HNDRD_udsResponse
    CHADA_UDSRESPONSE_MID       = 0x61F    # Chada_response
    TH_CMP_UDSRESPONSE_MID      = 0x613    # CMP_udsResponse
    TH_PTCR_UDSRESPONSE_MID     = 0x6D5    # PTCR_udsResponse
    BDY_SEC_UDSRESPONSE_MID     = 0x693    # SEC_udsResponse
    BDY_BC_UDSRESPONSE_MID      = 0x694    # BC_udsResponse
    BDY_PDM_UDSRESPONSE_MID     = 0x699    # PDM_udsResponse
    BDY_DDM_UDSRESPONSE_MID     = 0x69A    # DDM_udsResponse
    BDY_LFT_UDSRESPONSE_MID     = 0x69D    # LFT_udsResponse
    BDY_SNSCLL_UDSRESPONSE_MID  = 0x6f8    # SNSCLL_udsResponse
    BDY_SNSCLR1_UDSRESPONSE_MID = 0x6f9    # SNSCLR1_udsResponse
    BDY_SNSCUL1_UDSRESPONSE_MID = 0x6fd    # SNSCUL1_udsResponse
    SNSCUL_UDSRESPONSE_MID      = 0x6fd    # SNSCUL_udsResponse
    BDY_SNSCUR_UDSRESPONSE_MID  = 0x6ff    # SNSCUR_udsResponse
    BDY_SUN_UDSRESPONSE_MID     = 0x69E    # SUN_udsResponse
    BDY_TUNER_UDSRESPONSE_MID   = 0x69F    # TUNER_udsResponse
    BFT_PTC_UDSRESPONSE_MID     = 0x6D6    # PTC_udsResponse
    BFT_RCCM_UDSRESPONSE_MID    = 0x6D7    # RCCM_udsResponse
    BFT_MSM_UDSRESPONSE_MID     = 0x6DC    # MSM_udsResponse
    BFT_MSMD_UDSRESPONSE_MID    = 0x7ea    # node:MSMD
    BFT_MSMP_UDSRESPONSE_MID    = 0x7eb    # node:MSMP
    ETH_DCDC_UDSRESPONSE_MID    = 0x610    # DCDC_udsResponse
    ETH_BMS_UDSRESPONSE_MID     = 0x612    # BMS_udsResponse
    ETH_PM_UDSRESPONSE_MID      = 0x614    # PM_udsResponse
    ETH_DI_UDSRESPONSE_MID      = 0x616    # DI_udsResponse
    ETH_THC_UDSRESPONSE_MID     = 0x61A    # THC_udsResponse
    ETH_CHG_UDSRESPONSE_MID     = 0x61C    # CHG_udsResponse
    ETH_CP_UDSRESPONSE_MID      = 0x61E    # CP_udsResponse
    ETH_SDM_UDSRESPONSE_MID     = 0x651    # SDM_udsResponse
    ETH_OCS_UDSRESPONSE_MID     = 0x653    # OCS_udsResponse
    ETH_EPB_UDSRESPONSE_MID     = 0x654    # EPB_udsResponse
    ETH_ESP_UDSRESPONSE_MID     = 0x655    # ESP_udsResponse
    ETH_EPBM_UDSRESPONSE_MID    = 0x657    # EPBM_udsResponse
    ETH_EAS_UDSRESPONSE_MID     = 0x65B    # EAS_udsResponse
    ETH_IC_UDSRESPONSE_MID      = 0x65C    # IC_udsResponse
    ETH_PARK_UDSRESPONSE_MID    = 0x65E    # PARK_udsResponse
    ETH_TPMS_UDSRESPONSE_MID    = 0x65F    # TPMS_udsResponse
    ETH_SEC_UDSRESPONSE_MID     = 0x693    # SEC_udsResponse
    ETH_BC_UDSRESPONSE_MID      = 0x694    # BC_udsResponse
    ETH_DIS_UDSRESPONSE_MID     = 0x696    # DIS_udsResponse
    ETH_PDM_UDSRESPONSE_MID     = 0x699    # PDM_udsResponse
    ETH_DDM_UDSRESPONSE_MID     = 0x69A    # DDM_udsResponse
    ETH_CHGS_UDSRESPONSE_MID    = 0x69C    # CHGS_udsResponse
    ETH_LFT_UDSRESPONSE_MID     = 0x69D    # LFT_udsResponse
    ETH_SUN_UDSRESPONSE_MID     = 0x69E    # SUN_udsResponse
    ETH_TUNER_UDSRESPONSE_MID   = 0x69F    # TUNER_udsResponse
    ETH_PTC_UDSRESPONSE_MID     = 0x6D6    # PTC_udsResponse
    ETH_RCCM_UDSRESPONSE_MID    = 0x6D7    # RCCM_udsResponse
    ETH_MSM_UDSRESPONSE_MID     = 0x6DC    # MSM_udsResponse
    ETH_EPAS_UDSRESPONSE_MID    = 0x738    # EPAS_udsResponse
    ETH_SCCM_UDSRESPONSE_MID    = 0x798    # SCCM_udsResponse
    PT_HVBS_UDSRESPONSE_MID     = 0x60F    # HVBS_udsResponse
    PT_DCDC_UDSRESPONSE_MID     = 0x610    # DCDC_udsResponse
    PT_BMS_UDSRESPONSE_MID      = 0x612    # BMS_udsResponse
    PT_CMP_UDSRESPONSE_MID      = 0x613    # CMP_udsResponse
    PT_PM_UDSRESPONSE_MID       = 0x614    # PM_udsResponse
    PT_DIS_UDSRESPONSE_MID      = 0x615    # DIS_udsResponse
    PT_DI_UDSRESPONSE_MID       = 0x616    # DI_udsResponse
    PT_CHGPH1_UDSRESPONSE_MID   = 0x617    # CHGPH1_udsResponse
    PT_CHGPH2_UDSRESPONSE_MID   = 0x619    # CHGPH2_udsResponse
    PT_THC_UDSRESPONSE_MID      = 0x61A    # THC_udsResponse
    PT_CHGPH3_UDSRESPONSE_MID   = 0x61B    # CHGPH3_udsResponse
    PT_CHG_UDSRESPONSE_MID      = 0x61C    # CHG_udsResponse
    PT_CHGSPH2_UDSRESPONSE_MID  = 0x61D    # CHGSPH2_udsResponse
    PT_CP_UDSRESPONSE_MID       = 0x61E    # CP_udsResponse
    PT_CHGRLY_UDSRESPONSE_MID   = 0x63C    # CHGRLY_udsResponse
    PT_PMS_UDSRESPONSE_MID      = 0x654    # PMS_udsResponse
    PT_CHGSPH1_UDSRESPONSE_MID  = 0x697    # CHGSPH1_udsResponse
    PT_CHGSPH3_UDSRESPONSE_MID  = 0x69B    # CHGSPH3_udsResponse
    PT_CHGS_UDSRESPONSE_MID     = 0x69C    # CHGS_udsResponse
    CH_SDM_UDSRESPONSE_MID      = 0x651    # SDM_udsResponse
    CH_OCS_UDSRESPONSE_MID      = 0x653    # OCS_udsResponse
    CH_EPB_UDSRESPONSE_MID      = 0x654    # EPB_udsResponse
    CH_ESP_UDSRESPONSE_MID      = 0x655    # ESP_udsResponse
    CH_EPBM_UDSRESPONSE_MID     = 0x657    # EPBM_udsResponse
    CH_DAS_UDSRESPONSE_MID      = 0x659    # DAS_udsResponse
    CH_EAS_UDSRESPONSE_MID      = 0x65B    # EAS_udsResponse
    CH_IC_UDSRESPONSE_MID       = 0x65C    # IC_udsResponse
    CH_IBST_UDSRESPONSE_MID     = 0x65D    # IBST_udsResponse
    CH_PARK_UDSRESPONSE_MID     = 0x65E    # PARK_udsResponse
    CH_TPMS_UDSRESPONSE_MID     = 0x65F    # TPMS_udsResponse
    CH_RADC_UDSRESPONSE_MID     = 0x681    # RADC_udsResponse
    CH_RADRL_UDSRESPONSE_MID    = 0x682    # RADRL_udsResponse
    CH_RADRR_UDSRESPONSE_MID    = 0x683    # RADRR_udsResponse
    CH_RADFL_UDSRESPONSE_MID    = 0x684    # RADFL_udsResponse
    CH_RADFR_UDSRESPONSE_MID    = 0x685    # RADFR_udsResponse
    CH_EPAS_UDSRESPONSE_MID     = 0x738    # EPAS_udsResponse
    CH_SCCM_UDSRESPONSE_MID     = 0x798    # SCCM_udsResponse
    PT_BMS01_UDSRESPONSE_MID    = 0x631    # BMS01_udsResponse
    PT_BMS02_UDSRESPONSE_MID    = 0x632    # BMS02_udsResponse
    PT_BMS03_UDSRESPONSE_MID    = 0x633    # BMS03_udsResponse
    PT_BMS04_UDSRESPONSE_MID    = 0x634    # BMS04_udsResponse
    PT_BMS05_UDSRESPONSE_MID    = 0x635    # BMS05_udsResponse
    PT_BMS06_UDSRESPONSE_MID    = 0x636    # BMS06_udsResponse
    PT_BMS07_UDSRESPONSE_MID    = 0x637    # BMS07_udsResponse
    PT_BMS08_UDSRESPONSE_MID    = 0x638    # BMS08_udsResponse
    PT_BMS09_UDSRESPONSE_MID    = 0x639    # BMS09_udsResponse
    PT_BMS10_UDSRESPONSE_MID    = 0x63A    # BMS10_udsResponse
    PT_CHG01_UDSRESPONSE_MID    = 0x611    # CHG01_udsResponse
    PT_CHG02_UDSRESPONSE_MID    = 0x612    # CHG02_udsResponse
    PT_CHG03_UDSRESPONSE_MID    = 0x613    # CHG03_udsResponse
    PT_CHG04_UDSRESPONSE_MID    = 0x614    # CHG04_udsResponse
    PT_CHG05_UDSRESPONSE_MID    = 0x615    # CHG05_udsResponse
    PT_CHG06_UDSRESPONSE_MID    = 0x616    # CHG06_udsResponse
    PT_CHG07_UDSRESPONSE_MID    = 0x617    # CHG07_udsResponse
    PT_CHG08_UDSRESPONSE_MID    = 0x618    # CHG08_udsResponse
    PT_CHG09_UDSRESPONSE_MID    = 0x619    # CHG09_udsResponse
    PT_CHG10_UDSRESPONSE_MID    = 0x61A    # CHG10_udsResponse
    PT_CHG11_UDSRESPONSE_MID    = 0x61B    # CHG11_udsResponse
    PT_CHG12_UDSRESPONSE_MID    = 0x61C    # CHG12_udsResponse
    PT_SCS_UDSRESPONSE_MID      = 0x61E    # SCS_udsResponse
    PT_SCM_UDSRESPONSE_MID      = 0x61F    # SCM_udsResponse
    PT_CHG01PH1_UDSRESPONSE_MID  = 0x631    # CHG01PH1_udsResponse
    PT_CHG02PH1_UDSRESPONSE_MID  = 0x632    # CHG02PH1_udsResponse
    PT_CHG03PH1_UDSRESPONSE_MID  = 0x633    # CHG03PH1_udsResponse
    PT_CHG04PH1_UDSRESPONSE_MID  = 0x634    # CHG04PH1_udsResponse
    PT_CHG05PH1_UDSRESPONSE_MID  = 0x635    # CHG05PH1_udsResponse
    PT_CHG06PH1_UDSRESPONSE_MID  = 0x636    # CHG06PH1_udsResponse
    PT_CHG07PH1_UDSRESPONSE_MID  = 0x637    # CHG07PH1_udsResponse
    PT_CHG08PH1_UDSRESPONSE_MID  = 0x638    # CHG08PH1_udsResponse
    PT_CHG09PH1_UDSRESPONSE_MID  = 0x639    # CHG09PH1_udsResponse
    PT_CHG10PH1_UDSRESPONSE_MID  = 0x63A    # CHG10PH1_udsResponse
    PT_CHG11PH1_UDSRESPONSE_MID  = 0x63B    # CHG11PH1_udsResponse
    PT_CHG12PH1_UDSRESPONSE_MID  = 0x63C    # CHG12PH1_udsResponse
    PT_CHG01PH2_UDSRESPONSE_MID  = 0x651    # CHG01PH2_udsResponse
    PT_CHG02PH2_UDSRESPONSE_MID  = 0x652    # CHG02PH2_udsResponse
    PT_CHG03PH2_UDSRESPONSE_MID  = 0x653    # CHG03PH2_udsResponse
    PT_CHG04PH2_UDSRESPONSE_MID  = 0x654    # CHG04PH2_udsResponse
    PT_CHG05PH2_UDSRESPONSE_MID  = 0x655    # CHG05PH2_udsResponse
    PT_CHG06PH2_UDSRESPONSE_MID  = 0x656    # CHG06PH2_udsResponse
    PT_CHG07PH2_UDSRESPONSE_MID  = 0x657    # CHG07PH2_udsResponse
    PT_CHG08PH2_UDSRESPONSE_MID  = 0x658    # CHG08PH2_udsResponse
    PT_CHG09PH2_UDSRESPONSE_MID  = 0x659    # CHG09PH2_udsResponse
    PT_CHG10PH2_UDSRESPONSE_MID  = 0x65A    # CHG10PH2_udsResponse
    PT_CHG11PH2_UDSRESPONSE_MID  = 0x65B    # CHG11PH2_udsResponse
    PT_CHG12PH2_UDSRESPONSE_MID  = 0x65C    # CHG12PH2_udsResponse
    PT_CHG01PH3_UDSRESPONSE_MID  = 0x671    # CHG01PH3_udsResponse
    PT_CHG02PH3_UDSRESPONSE_MID  = 0x672    # CHG02PH3_udsResponse
    PT_CHG03PH3_UDSRESPONSE_MID  = 0x673    # CHG03PH3_udsResponse
    PT_CHG04PH3_UDSRESPONSE_MID  = 0x674    # CHG04PH3_udsResponse
    PT_CHG05PH3_UDSRESPONSE_MID  = 0x675    # CHG05PH3_udsResponse
    PT_CHG06PH3_UDSRESPONSE_MID  = 0x676    # CHG06PH3_udsResponse
    PT_CHG07PH3_UDSRESPONSE_MID  = 0x677    # CHG07PH3_udsResponse
    PT_CHG08PH3_UDSRESPONSE_MID  = 0x678    # CHG08PH3_udsResponse
    PT_CHG09PH3_UDSRESPONSE_MID  = 0x679    # CHG09PH3_udsResponse
    PT_CHG10PH3_UDSRESPONSE_MID  = 0x67A    # CHG10PH3_udsResponse
    PT_CHG11PH3_UDSRESPONSE_MID  = 0x67B    # CHG11PH3_udsResponse
    PT_CHG12PH3_UDSRESPONSE_MID  = 0x67C    # CHG12PH3_udsResponse
    VC_VCFRONT_UDSRESPONSE_MID = 0x601
    VC_VCLEFT_UDSRESPONSE_MID  = 0x623
    VC_VCRIGHT_UDSRESPONSE_MID = 0x609
    VC_VCSEC_UDSRESPONSE_MID   = 0x60B
    VC_EPBL_UDSRESPONSE_MID    = 0x625
    VC_EBPR_UDSRESPONSE_MID    = 0x627


if __name__ == "__main__":
    print __doc__
    print RespID.__doc__
