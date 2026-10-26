"""Networking tests (ticket 05) — sandbox slice.

The LibvirtBackend behaviour tests (interface attach, missing-network guard)
live in test_libvirt_backend.py against the shared fake-libvirt harness. This
file covers the shipped host-setup XML files and the FakeBackend's net flag.
Real packet behaviour (ping out ✅ / ping other qube ❌) is the owner-machine
checklist — here we prove file shapes and recorded state only.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from miniqubes.backends import FakeBackend
from miniqubes.core import Qube

REPO = Path(__file__).resolve().parent.parent
NET_XML = REPO / "tools" / "mq-net.xml"
NWFILTER = REPO / "tools" / "mq-isolate.nwfilter"


class HostSetupFilesTest(unittest.TestCase):
    def test_network_xml_is_the_nat_net_qubes_expects(self):
        text = NET_XML.read_text(encoding="utf-8")
        self.assertIn("<name>mq-net</name>", text)
        self.assertIn("forward mode='nat'", text)
        self.assertIn("10.137.0.1", text)                    # gateway
        self.assertIn("start='10.137.0.2'", text)            # DHCP range start
        self.assertIn("end='10.137.0.254'", text)            # DHCP range end

    def test_nwfilter_drops_qube_subnet_but_not_gateway_nor_internet(self):
        text = NWFILTER.read_text(encoding="utf-8")
        self.assertIn("name='mq-isolate'", text)
        self.assertIn("action='drop'", text)
        self.assertIn("dstipfrom='10.137.0.2'", text)        # first qube IP
        self.assertIn("dstipto='10.137.0.254'", text)        # last qube IP
        # gateway (.1) and everything outside the subnet fall through to accept
        self.assertIn("action='accept'", text)
        self.assertIn("<all", text)


class FakeBackendNetFlagTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.backend = FakeBackend(Path(self._tmp.name) / "state.json")

    def test_create_records_net_true(self):
        self.backend.create(Qube(name="personal", template="noble"))
        row = json.loads(self.backend.path.read_text())["qubes"]["personal"]
        self.assertTrue(row["net"])

    def test_qube_and_therefore_mq_list_stay_unchanged(self):
        # network is backend detail — it must not leak into the Qube model
        self.assertEqual([f.name for f in Qube.__dataclass_fields__.values()],
                         ["name", "template", "state"])


if __name__ == "__main__":
    unittest.main()
