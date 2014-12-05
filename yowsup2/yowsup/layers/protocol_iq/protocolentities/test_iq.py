from yowsup.layers.protocol_iq.protocolentities.iq import IqProtocolEntity
from yowsup.structs import ProtocolTreeNode
from yowsup.structs.protocolentity import ProtocolEntityTest

class IqProtocolEntityTest(ProtocolEntityTest):
    def setUp(self):
        self.ProtocolEntity = IqProtocolEntity
        self.node = ProtocolTreeNode("iq", {"id": "test_id", "type": "get", "xmlns": "iq_xmlns"}, None, None)