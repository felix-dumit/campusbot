from yowsup.layers.protocol_presence.protocolentities.presence import PresenceProtocolEntity
from yowsup.structs import ProtocolTreeNode
from yowsup.structs.protocolentity import ProtocolEntityTest

class PresenceProtocolEntityTest(ProtocolEntityTest):
    def setUp(self):
        self.ProtocolEntity = PresenceProtocolEntity
        self.node = ProtocolTreeNode("presence", {"type": "presence_type", "name": "presence_name"}, None, None)
