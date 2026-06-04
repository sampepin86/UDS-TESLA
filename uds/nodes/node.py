"""
node.py
Created on Apr 18, 2016

@author: jpetrie

@description: Nodes is the definition and container for Known Tesla (and vendor) UDS Nodes.

"""

from boot_id import BootID
from bus_id import BusID
from component_id import ComponentID
from message_id import Message
from mplexor_id import Mplexor
from node_id import NodeID
from req_id import ReqID
from resp_id import RespID
from vendor_id import VendorID
from version_id import VersionLen, VersionOff


class Node(object):
    """
    Node is a container for Node UDS data.
    """

    def __init__(self, name="",
                 nodeName="",
                 componentID=ComponentID.NONE,
                 nodeID=NodeID.UDS_NODE_NONE,
                 requestID=ReqID.UDS_NONE_MID,
                 responseID=RespID.UDS_NONE_MID,
                 bootID=BootID.NONE_BOOT_MID,
                 mau=1,
                 pnSn=0,
                 versionMsgId=Message.NONE_MID,
                 versionLength=VersionLen.TESLA_CRC_LEN,
                 versionOffset=VersionOff.UDS_TESLA_DID_APP_CRC_OFFSET,
                 vendorID=VendorID.UDS_VENDOR_UNKNOWN,
                 busID=BusID.UDS_BUS_NONE,
                 mplexedVersionMsg=False,
                 mplexor=Mplexor.UNKNOWN_MPLEXOR
                 ):
        """
        Constructor.  Not much here for a container class.
        """

        self.name = name
        self.nodeName = nodeName
        self.componentID = componentID
        self.nodeID = nodeID
        self.requestID = requestID
        self.responseID = responseID
        self.bootID = bootID
        self.mau = mau

        self.pnSn = pnSn
        self.versionMsgId = versionMsgId
        self.versionLength = versionLength
        self.versionOffset = versionOffset
        self.vendorID = vendorID
        self.busID = busID
        self.mplexedVersionMsg = mplexedVersionMsg
        self.mplexor = mplexor

        self.test()

    def __repr__(self):
        """
        Represent!
        """
        return "<UDS Node {0} at 0x{1:x}>".format(self.name, id(self))

    def __str__(self):
        """
        String for printing.
        """
        parts = ["{class_name}: {name}\n"
                 "    Name: {node_name}\n"
                 "    Component ID: {comp_id:#x} ({comp_name})\n"
                 "    Node ID: {node_id}\n"
                 "    Bus ID: {bus_id:#x} ({bus_name})\n"
                     .format(class_name=self.__class__.__name__,
                             name=self.name,
                             node_name=self.nodeName,
                             comp_id=self.componentID.value,
                             comp_name=self.componentID.name,
                             node_id=self.nodeID.name,
                             bus_name=self.busID.name,
                             bus_id=self.busID.value),
                 "    Request ID: {req_id:#x} ({req_name})\n"
                 "    Response ID: {resp_id:#x} ({resp_name})\n"
                 "    Boot ID: {boot_id:#x} ({boot_name})\n"
                 "    MAU: {mau}\n"
                     .format(req_id=self.requestID.value,
                             req_name=self.requestID.name,
                             resp_id=self.responseID.value,
                             resp_name=self.responseID.name,
                             boot_id=self.bootID.value,
                             boot_name=self.bootID.name,
                             mau=self.mau),
                 "    Version Msg ID: {ver_id:#x} ({ver_name})\n"
                 "    Version Length: {ver_len:#x} ({ver_len_name})\n"
                 "    Version Offset: {ver_off:#x} ({ver_off_name})\n"
                 "    Multiplexed Version Msg: {mplexedVerMsg}\n"
                 "    Multiplexor: {mplexor:#x} ({mplexor_name})\n"
                     .format(ver_id=self.versionMsgId.value,
                             ver_name=self.versionMsgId.name,
                             ver_len=self.versionLength.value,
                             ver_len_name=self.versionLength.name,
                             ver_off=self.versionOffset.value,
                             ver_off_name=self.versionOffset.name,
                             mplexedVerMsg=self.mplexedVersionMsg,
                             mplexor=self.mplexor.value,
                             mplexor_name=self.mplexor.name),
                 "    Version Msg ID: {vendor_id:#x} ({vendor_name})\n"
                 "    pnsn: {pnsn:#x}\n"
                     .format(vendor_id=self.vendorID.value,
                             vendor_name=self.vendorID.name,
                             pnsn=self.pnSn)]

        strVer = ''.join(parts)

        return strVer

    def __eq__(self, other):
        return (self.name == other.name and
                self.nodeName == other.nodeName and
                self.componentID == other.componentID and
                self.nodeID == other.nodeID and
                self.requestID == other.requestID and
                self.responseID == other.responseID and
                self.bootID == other.bootID and
                self.mau == other.mau and
                self.pnSn == other.pnSn and
                self.versionMsgId == other.versionMsgId and
                self.versionLength == other.versionLength and
                self.versionOffset == other.versionOffset and
                self.vendorID == other.vendorID and
                self.busID == other.busID and
                self.mplexedVersionMsg == other.mplexedVersionMsg and
                self.mplexor == other.mplexor)

    def test(self):
        """
        Test runs some simple checks to make sure the instance is valid.
        """

        assert isinstance(self.name, basestring), "name should be string"
        assert isinstance(self.nodeName, basestring), "nodeName should be string"
        assert isinstance(self.componentID, ComponentID), "componentID should be enum of ComponentID"
        assert isinstance(self.nodeID, NodeID), "nodeID should be an enum of NodeID"
        assert isinstance(self.requestID, ReqID), "requestID should be an enum of ReqID"
        assert isinstance(self.responseID, RespID), "responseID should be an enum of RespID"
        assert isinstance(self.bootID, BootID), "bootID should be an enum of BootID"
        assert isinstance(self.mau, int), "mau should be int"
        assert isinstance(self.pnSn, int), "pnSn should be int"
        assert isinstance(self.versionMsgId, Message), "versionMsgId should be Message"
        assert isinstance(self.versionLength, VersionLen), "versionLength should be VersionLen"
        assert isinstance(self.versionOffset, VersionOff), "versionOffset should be VersionOff"
        assert isinstance(self.vendorID, VendorID), "vendorID should be VendorID"
        assert isinstance(self.busID, BusID), "busID should be BusID"
        assert isinstance(self.mplexedVersionMsg, bool) or self.mplexor is None, "mplexedVersionMsg should be bool"
        assert isinstance(self.mplexor, Mplexor) or self.mplexor is None, "mplexor should be Mplexor"

    def serialize(self):
        """
        Serialize returns a dictionary of self.
        :return nodeDict: <dict> self as dictionary.
        """
        nodeDict = {"nodeName": self.nodeName,
                    "componentID": int(self.componentID),
                    "nodeID": str(self.nodeID),
                    "reqID": int(self.requestID),
                    "respID": int(self.responseID),
                    "bootID": int(self.bootID),
                    "mau": int(self.mau),
                    "pnSn": int(self.pnSn),
                    "versionMsgId": int(self.versionMsgId),
                    "versionLength": int(self.versionLength),
                    "versionOffset": int(self.versionOffset),
                    "vendorID": int(self.vendorID),
                    "busID": int(self.busID),
                    "mplexedVersionMsg": bool(self.mplexedVersionMsg),
                    "mplexor": int(self.mplexor)
                    }

        return nodeDict

    def deserialize(self, nodeDict, name=""):
        """
        Deserialize converts self into incoming dictionary.
        :param nodeDict: <dict> a dictionary version of a Node.
        :param name: <string> amazingly the name of the node can be different than the nodeName.
        :return self: <Node> a reference to self.
        """

        self.name = name
        self.nodeName = nodeDict["nodeName"]
        self.componentID = ComponentID(nodeDict["componentID"])
        self.nodeID = getattr(NodeID, nodeDict["nodeID"])
        self.busID = BusID(nodeDict["busID"])
        self.requestID = ReqID(nodeDict["reqID"])
        self.responseID = RespID(nodeDict["respID"])
        self.bootID = BootID(nodeDict["bootID"])
        self.mau = nodeDict["mau"]
        self.pnSn = nodeDict["pnSn"]
        self.versionMsgId = Message(nodeDict["versionMsgId"])
        self.versionLength = VersionLen(nodeDict["versionLength"])
        self.versionOffset = VersionOff(nodeDict["versionOffset"])
        self.vendorID = VendorID(nodeDict["vendorID"])
        self.mplexedVersionMsg = bool(nodeDict["mplexedVersionMsg"])
        self.mplexor = Mplexor(nodeDict["mplexor"])

        self.test()

        return self


if __name__ == "__main__":
    print __doc__
    print Node.__doc__
