"""
req_id.py
Created on Apr 18, 2016

@author: jpetrie

@description: ReqID is the definition and container for Known Tesla (and vendor) UDS Request CAN IDs.
              This information is somewhat duplicated in the nodes.json. nodes.json is the source of truth, this file
              must match. It provides an easy/separate interface for development.

"""
from enum import IntEnum


# noinspection PyPep8,PyPep8
class ReqID(IntEnum):
    """
    The CAN IDs for the Request Message
    """
    UDS_NONE_MID                = 0x000    # NONE/ bounds checking
    UDS_LMREQUEST_MID           = 0x001    # LM_usdRequest
    UDS_LSREQUEST_MID           = 0x002    # LS_usdRequest
    BDY_UDS_BCCENREQUEST_MID    = 0x681    # UDS_bccenRequest
    BDY_UDS_BCREARREQUEST_MID   = 0x6A2    # UDS_bcrearRequest
    BDY_UDS_BCFRONTREQUEST_MID  = 0x6A3    # UDS_bcfrontRequest
    BDY_UDS_BCFDMREQUEST_MID    = 0x6A4    # UDS_bcfdmRequest
    BDY_UDS_BCFPMREQUEST_MID    = 0x6A5    # UDS_bcfpmRequest
    BDY_UDS_BCRDMREQUEST_MID    = 0x6A6    # UDS_bcrdmRequest
    BDY_UDS_BCRPMREQUEST_MID    = 0x6A7    # UDS_bcrpmRequest
    BDY_UDS_BCFALCREQUEST_MID   = 0x6A9    # UDS_bcfalcRequest
    BDY_UDS_BCFALCDREQUEST_MID  = 0x6AE    # UDS_bcfalcdRequest
    BDY_UDS_BCFALCPREQUEST_MID  = 0x6AA    # UDS_bcfalcpRequest
    BDY_UDS_BCS2LREQUEST_MID    = 0x6AB    # UDS_bcs2lRequest
    BDY_UDS_BCS2CREQUEST_MID    = 0x6AC    # UDS_bcs2cRequest
    BDY_UDS_BCS2RREQUEST_MID    = 0x6AD    # UDS_bcs2rRequest
    BDY_UDS_DHFDREQUEST_MID     = 0x128    # UDS_DHFDRequest
    BDY_UDS_DHRDREQUEST_MID     = 0x128    # UDS_DHRDRequest
    BDY_UDS_DHFPREQUEST_MID     = 0x138    # UDS_DHFPRequest
    BDY_UDS_DHRPREQUEST_MID     = 0x138    # UDS_DHRPRequest
    BDY_UDS_HNDFDREQUEST_MID    = 0x128    # UDS_HNDFDRequest
    BDY_UDS_HNDRDREQUEST_MID    = 0x128    # UDS_HNDRDRequest
    BDY_UDS_HNDFPREQUEST_MID    = 0x138    # UDS_HNDFPRequest
    BDY_UDS_HNDRPREQUEST_MID    = 0x138    # UDS_HNDRPRequest
    UDS_CHADAREQUEST_MID        = 0x60F    # CHadaRequest
    TH_UDS_CMPREQUEST_MID       = 0x603    # UDS_cmpRequest
    TH_UDS_THCREQUEST_MID       = 0x60A    # UDS_thcRequest
    TH_UDS_PTCRREQUEST_MID      = 0x6C5    # UDS_ptcrRequest
    BDY_UDS_SECREQUEST_MID      = 0x683    # UDS_secRequest
    BDY_UDS_BDYREQUEST_MID      = 0x684    # UDS_bdyRequest
    BDY_UDS_PDMREQUEST_MID      = 0x689    # UDS_pdmRequest
    BDY_UDS_DDMREQUEST_MID      = 0x68A    # UDS_ddmRequest
    BDY_UDS_LFTREQUEST_MID      = 0x68D    # UDS_lftRequest
    BDY_UDS_SNSCLLREQUEST_MID   = 0x6e8    # UDS_SNSCLLRequest
    BDY_UDS_SNSCLR1REQUEST_MID  = 0x6e9    # UDS_SNSCLR1Request
    BDY_UDS_SNSCUL1REQUEST_MID  = 0x6ed    # UDS_SNSCUL1Request
    UDS_SNSCULREQUEST_MID       = 0x6ed    # UDS_SNSCULRequest
    BDY_UDS_SNSCURREQUEST_MID   = 0x6ef    # UDS_SNSCURRequest
    BDY_UDS_SUNREQUEST_MID      = 0x68E    # UDS_sunRequest
    BFT_UDS_PTCREQUEST_MID      = 0x6C6    # UDS_ptcRequest
    BFT_UDS_RCCMREQUEST_MID     = 0x6C7    # UDS_rccmRequest
    BFT_UDS_MSMREQUEST_MID      = 0x6CC    # UDS_msmRequest
    BFT_UDS_MSMDREQUEST_MID     = 0x7e2    # UDS_msmdRequest
    BFT_UDS_MSMPREQUEST_MID     = 0x7e3    # UDS_msmpRequest
    ETH_UDS_TUNERREQUEST_MID    = 0x68F    # UDS_tunerRequest
    PT_UDS_DCDCREQUEST_MID      = 0x600    # UDS_dcdcRequest
    PT_UDS_BMSREQUEST_MID       = 0x602    # UDS_bmsRequest
    PT_UDS_CMPREQUEST_MID       = 0x603    # UDS_cmpRequest
    PT_UDS_PMREQUEST_MID        = 0x604    # UDS_pmRequest
    PT_UDS_PMSREQUEST_MID       = 0x644    # UDS_pmsrequest
    PT_UDS_DISREQUEST_MID       = 0x605    # UDS_disRequest
    PT_UDS_DIREQUEST_MID        = 0x606    # UDS_diRequest
    PT_UDS_CHGPH1REQUEST_MID    = 0x607    # UDS_chgph1Request
    PT_UDS_CHGPH2REQUEST_MID    = 0x609    # UDS_chgph2Request
    PT_UDS_THCREQUEST_MID       = 0x60A    # UDS_thcRequest
    PT_UDS_CHGPH3REQUEST_MID    = 0x60B    # UDS_chgph3Request
    PT_UDS_CHGREQUEST_MID       = 0x60C    # UDS_chgRequest
    PT_UDS_CHGSPH2REQUEST_MID   = 0x60D    # UDS_chgsph2Request
    PT_UDS_CPREQUEST_MID        = 0x60E    # UDS_cpRequest
    PT_UDS_HVDSREQUEST_MID      = 0x61F    # UDS_hvdsRequest
    PT_UDS_CCREQUEST_MID        = 0x622    # UDS_ccRequest
    PT_UDS_CHGRLYREQUEST_MID    = 0x62C    # UDS_chgrlyRequest
    PT_UDS_CHGSPH1REQUEST_MID   = 0x687    # UDS_chgsph1Request
    PT_UDS_CHGSPH3REQUEST_MID   = 0x68B    # UDS_chgsph3Request
    PT_UDS_CHGSREQUEST_MID      = 0x68C    # UDS_chgsRequest
    CH_UDS_SDMREQUEST_MID       = 0x641    # UDS_sdmRequest
    CH_UDS_OCSREQUEST_MID       = 0x643    # UDS_ocsRequest
    CH_UDS_EPBREQUEST_MID       = 0x644    # UDS_epbRequest
    CH_UDS_ESPREQUEST_MID       = 0x645    # UDS_espRequest
    CH_UDS_EPBMREQUEST_MID      = 0x647    # UDS_epbmRequest
    CH_UDS_DASREQUEST_MID       = 0x649    # UDS_dasRequest
    CH_UDS_EASREQUEST_MID       = 0x64B    # UDS_easRequest
    CH_UDS_ICREQUEST_MID        = 0x64C    # UDS_icRequest
    CH_UDS_IBSTREQUEST_MID      = 0x64D    # UDS_ibstRequest
    CH_UDS_PARKREQUEST_MID      = 0x64E    # UDS_parkRequest
    CH_UDS_TPMSREQUEST_MID      = 0x64F    # UDS_tpmsRequest
    CH_UDS_RADCREQUEST_MID      = 0x671    # UDS_radcRequest
    CH_UDS_RADRLREQUEST_MID     = 0x672    # UDS_radrlRequest
    CH_UDS_RADRRREQUEST_MID     = 0x673    # UDS_radrrRequest
    CH_UDS_RADFLREQUEST_MID     = 0x674    # UDS_radflRequest
    CH_UDS_RADFRREQUEST_MID     = 0x675    # UDS_radfrRequest
    CH_UDS_SCCMREQUEST_MID      = 0x790    # UDS_sccmRequest
    CH_UDS_EPASREQUEST_MID      = 0x730    # UDS_epasRequest
    PT_UDS_BMSREQUEST_BMS01_MID = 0x621    # UDS_bmsRequest_BMS01
    PT_UDS_BMSREQUEST_BMS02_MID = 0x0622    # UDS_bmsRequest_BMS02
    PT_UDS_BMSREQUEST_BMS03_MID = 0x623    # UDS_bmsRequest_BMS03
    PT_UDS_BMSREQUEST_BMS04_MID = 0x624    # UDS_bmsRequest_BMS04
    PT_UDS_BMSREQUEST_BMS05_MID = 0x625    # UDS_bmsRequest_BMS05
    PT_UDS_BMSREQUEST_BMS06_MID = 0x626    # UDS_bmsRequest_BMS06
    PT_UDS_BMSREQUEST_BMS07_MID = 0x627    # UDS_bmsRequest_BMS07
    PT_UDS_BMSREQUEST_BMS08_MID = 0x628    # UDS_bmsRequest_BMS08
    PT_UDS_BMSREQUEST_BMS09_MID = 0x629    # UDS_bmsRequest_BMS09
    PT_UDS_BMSREQUEST_BMS10_MID = 0x62A    # UDS_bmsRequest_BMS10
    PT_UDS_CHGREQUEST_CHG01_MID = 0x601    # UDS_chgRequest_CHG01
    PT_UDS_CHGREQUEST_CHG02_MID = 0x602    # UDS_chgRequest_CHG02
    PT_UDS_CHGREQUEST_CHG03_MID = 0x603    # UDS_chgRequest_CHG03
    PT_UDS_CHGREQUEST_CHG04_MID = 0x604    # UDS_chgRequest_CHG04
    PT_UDS_CHGREQUEST_CHG05_MID = 0x605    # UDS_chgRequest_CHG05
    PT_UDS_CHGREQUEST_CHG06_MID = 0x606    # UDS_chgRequest_CHG06
    PT_UDS_CHGREQUEST_CHG07_MID = 0x607    # UDS_chgRequest_CHG07
    PT_UDS_CHGREQUEST_CHG08_MID = 0x608    # UDS_chgRequest_CHG08
    PT_UDS_CHGREQUEST_CHG09_MID = 0x609    # UDS_chgRequest_CHG09
    PT_UDS_CHGREQUEST_CHG10_MID = 0x60A    # UDS_chgRequest_CHG10
    PT_UDS_CHGREQUEST_CHG11_MID = 0x60B    # UDS_chgRequest_CHG11
    PT_UDS_CHGREQUEST_CHG12_MID = 0x60C    # UDS_chgRequest_CHG12
    PT_UDS_SCSREQUEST_MID       = 0x60E    # UDS_scsRequest
    PT_UDS_SCMREQUEST_MID       = 0x60F    # UDS_scmRequest
    PT_UDS_CHGPH1REQUEST_CHG01_MID = 0x621    # UDS_chgph1Request_CHG01
    PT_UDS_CHGPH1REQUEST_CHG02_MID = 0x622    # UDS_chgph1Request_CHG02
    PT_UDS_CHGPH1REQUEST_CHG03_MID = 0x623    # UDS_chgph1Request_CHG03
    PT_UDS_CHGPH1REQUEST_CHG04_MID = 0x624    # UDS_chgph1Request_CHG04
    PT_UDS_CHGPH1REQUEST_CHG05_MID = 0x625    # UDS_chgph1Request_CHG05
    PT_UDS_CHGPH1REQUEST_CHG06_MID = 0x626    # UDS_chgph1Request_CHG06
    PT_UDS_CHGPH1REQUEST_CHG07_MID = 0x627    # UDS_chgph1Request_CHG07
    PT_UDS_CHGPH1REQUEST_CHG08_MID = 0x628    # UDS_chgph1Request_CHG08
    PT_UDS_CHGPH1REQUEST_CHG09_MID = 0x629    # UDS_chgph1Request_CHG09
    PT_UDS_CHGPH1REQUEST_CHG10_MID = 0x62A    # UDS_chgph1Request_CHG10
    PT_UDS_CHGPH1REQUEST_CHG11_MID = 0x62B    # UDS_chgph1Request_CHG11
    PT_UDS_CHGPH1REQUEST_CHG12_MID = 0x62C    # UDS_chgph1Request_CHG12
    PT_UDS_CHGPH2REQUEST_CHG01_MID = 0x641    # UDS_chgph2Request_CHG01
    PT_UDS_CHGPH2REQUEST_CHG02_MID = 0x642    # UDS_chgph2Request_CHG02
    PT_UDS_CHGPH2REQUEST_CHG03_MID = 0x643    # UDS_chgph2Request_CHG03
    PT_UDS_CHGPH2REQUEST_CHG04_MID = 0x644    # UDS_chgph2Request_CHG04
    PT_UDS_CHGPH2REQUEST_CHG05_MID = 0x645    # UDS_chgph2Request_CHG05
    PT_UDS_CHGPH2REQUEST_CHG06_MID = 0x646    # UDS_chgph2Request_CHG06
    PT_UDS_CHGPH2REQUEST_CHG07_MID = 0x647    # UDS_chgph2Request_CHG07
    PT_UDS_CHGPH2REQUEST_CHG08_MID = 0x648    # UDS_chgph2Request_CHG08
    PT_UDS_CHGPH2REQUEST_CHG09_MID = 0x649    # UDS_chgph2Request_CHG09
    PT_UDS_CHGPH2REQUEST_CHG10_MID = 0x64A    # UDS_chgph2Request_CHG10
    PT_UDS_CHGPH2REQUEST_CHG11_MID = 0x64B    # UDS_chgph2Request_CHG11
    PT_UDS_CHGPH2REQUEST_CHG12_MID = 0x64C    # UDS_chgph2Request_CHG12
    PT_UDS_CHGPH3REQUEST_CHG01_MID = 0x661    # UDS_chgph3Request_CHG01
    PT_UDS_CHGPH3REQUEST_CHG02_MID = 0x662    # UDS_chgph3Request_CHG02
    PT_UDS_CHGPH3REQUEST_CHG03_MID = 0x663    # UDS_chgph3Request_CHG03
    PT_UDS_CHGPH3REQUEST_CHG04_MID = 0x664    # UDS_chgph3Request_CHG04
    PT_UDS_CHGPH3REQUEST_CHG05_MID = 0x665    # UDS_chgph3Request_CHG05
    PT_UDS_CHGPH3REQUEST_CHG06_MID = 0x666    # UDS_chgph3Request_CHG06
    PT_UDS_CHGPH3REQUEST_CHG07_MID = 0x667    # UDS_chgph3Request_CHG07
    PT_UDS_CHGPH3REQUEST_CHG08_MID = 0x668    # UDS_chgph3Request_CHG08
    PT_UDS_CHGPH3REQUEST_CHG09_MID = 0x669    # UDS_chgph3Request_CHG09
    PT_UDS_CHGPH3REQUEST_CHG10_MID = 0x66A    # UDS_chgph3Request_CHG10
    PT_UDS_CHGPH3REQUEST_CHG11_MID = 0x66B    # UDS_chgph3Request_CHG11
    PT_UDS_CHGPH3REQUEST_CHG12_MID = 0x66C    # UDS_chgph3Request_CHG12
    VC_UDS_VCFRONTREQUEST_MID = 0x600
    VC_UDS_VCLEFTREQUEST_MID  = 0x622
    VC_UDS_VCRIGHTREQUEST_MID = 0x608
    VC_UDS_VCSECREQUEST_MID   = 0x60A
    VC_UDS_VCEBPLREQUEST_MID  = 0x624
    VC_UDS_VCEPBRREQUEST_MID  = 0x626


if __name__ == "__main__":
    print __doc__
    print ReqID.__doc__
