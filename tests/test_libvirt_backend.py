"""LibvirtBackend tests (ticket 02) — run against a fake `libvirt` module.

shortcut: the sandbox has no libvirt/KVM, so these tests verify XML
generation, state mapping, and call behaviour only. Real VM boot is verified
on the owner's machine (guide Step 6) before ticket 02 can close.
"""
import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from miniqubes.backends import (AGENT_VSOCK_PORT, FakeBackend, LibvirtBackend,
                                default_backend)
from miniqubes.core import Qube, QubesError, RUNNING, STOPPED

VIR_DOMAIN_RUNNING = 1
VIR_DOMAIN_SHUTOFF = 5


class FakeLibvirtError(Exception):
    pass


class FakeDomain:
    def __init__(self, conn, name, xml):
        self._conn = conn
        self._name = name
        self._xml = xml
        self._state = VIR_DOMAIN_SHUTOFF
        self.stubborn = False          # True → shutdown() is ignored by the "guest"
        self.destroy_called = False

    def name(self):
        return self._name

    def state(self):
        return [self._state, 0]

    def create(self):
        self._state = VIR_DOMAIN_RUNNING

    def shutdown(self):
        if not self.stubborn:
            self._state = VIR_DOMAIN_SHUTOFF

    def destroy(self):
        self.destroy_called = True
        self._state = VIR_DOMAIN_SHUTOFF

    def undefine(self):
        self._conn.domains.pop(self._name, None)

    def XMLDesc(self):
        return self._xml


class FakeConn:
    def __init__(self):
        self.domains = {}
        self.defined_xml = []
        self._next_cid = 3

    def defineXML(self, xml):
        name = re.search(r"<name>([^<]+)</name>", xml).group(1)
        # like real libvirt: an auto-assigned CID comes back in the domain XML
        xml = xml.replace("auto='yes'", f"auto='yes' address='{self._next_cid}'")
        self._next_cid += 1
        dom = FakeDomain(self, name, xml)
        self.domains[name] = dom
        self.defined_xml.append(xml)
        return dom

    def lookupByName(self, name):
        if name not in self.domains:
            raise FakeLibvirtError(f"no domain with name {name!r}")
        return self.domains[name]

    def listAllDomains(self, flags=0):
        return list(self.domains.values())


def make_fake_libvirt():
    mod = types.ModuleType("libvirt")
    mod.libvirtError = FakeLibvirtError
    mod.VIR_DOMAIN_RUNNING = VIR_DOMAIN_RUNNING
    mod.VIR_DOMAIN_SHUTOFF = VIR_DOMAIN_SHUTOFF
    conn = FakeConn()
    mod.open = lambda uri: conn
    mod._conn = conn
    return mod


class LibvirtBackendTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.disks = Path(self._tmp.name) / "disks"
        self.disks.mkdir()
        (self.disks / "debian.qcow2").write_bytes(b"FAKEQCOW-plain")
        self.fake = make_fake_libvirt()
        patcher = mock.patch.dict(sys.modules, {"libvirt": self.fake})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.backend = LibvirtBackend(disks_dir=self.disks,
                                      stop_timeout=0.3, poll_interval=0.01)
        self.conn = self.fake._conn

    def _create(self, name="personal", template="debian"):
        self.backend.create(Qube(name=name, template=template))

    def test_create_defines_domain_and_copies_template_disk(self):
        self._create()
        self.assertEqual((self.disks / "personal.qcow2").read_bytes(),
                         b"FAKEQCOW-plain")
        xml = self.conn.defined_xml[0]
        self.assertIn("<name>mq-personal</name>", xml)
        self.assertIn("<vsock", xml)
        self.assertIn("auto='yes'", xml)        # CID auto-assign, guide Step 4b
        self.assertIn("virtio", xml)
        self.assertIn("debian", xml)            # template recorded in <metadata>
        self.assertIn(str(self.disks / "personal.qcow2"), xml)

    def test_create_without_template_is_a_clean_error(self):
        with self.assertRaises(QubesError):
            self.backend.create(Qube(name="notemplate"))

    def test_create_with_missing_template_disk_is_a_clean_error(self):
        with self.assertRaises(QubesError):
            self._create(name="ghost", template="does-not-exist")
        self.assertNotIn("mq-ghost", self.conn.domains)

    def test_create_accepts_img_template_disk(self):
        # guide Step 3 downloads noble-server-cloudimg-amd64.img
        (self.disks / "noble.img").write_bytes(b"CLOUDIMG")
        self._create(name="work", template="noble")
        self.assertEqual((self.disks / "work.qcow2").read_bytes(), b"CLOUDIMG")

    def test_start_stop_graceful(self):
        self._create()
        self.backend.start("personal")
        self.assertEqual(self.backend.get("personal").state, RUNNING)
        self.backend.stop("personal")
        dom = self.conn.domains["mq-personal"]
        self.assertFalse(dom.destroy_called)   # graceful first, no force needed
        self.assertEqual(self.backend.get("personal").state, STOPPED)

    def test_stop_falls_back_to_destroy(self):
        self._create()
        self.backend.start("personal")
        self.conn.domains["mq-personal"].stubborn = True
        self.backend.stop("personal")          # guest ignores shutdown → force
        dom = self.conn.domains["mq-personal"]
        self.assertTrue(dom.destroy_called)
        self.assertEqual(self.backend.get("personal").state, STOPPED)

    def test_get_and_list_map_state_and_template(self):
        self._create("personal")
        self._create("work")
        self.backend.start("work")
        by_name = {q.name: q for q in self.backend.list()}
        self.assertEqual(set(by_name), {"personal", "work"})
        self.assertEqual(by_name["work"].state, RUNNING)
        self.assertEqual(by_name["personal"].state, STOPPED)
        self.assertEqual(by_name["personal"].template, "debian")
        self.assertIsNone(self.backend.get("missing"))

    def test_list_ignores_foreign_domains(self):
        self.conn.defineXML("<domain><name>someone-elses-vm</name></domain>")
        self._create()
        self.assertEqual([q.name for q in self.backend.list()], ["personal"])

    def test_agent_endpoint_reads_cid_from_domain_xml(self):
        self._create()
        self.assertEqual(self.backend.agent_endpoint("personal"),
                         ("vsock", 3, AGENT_VSOCK_PORT))
        self._create("work")
        self.assertEqual(self.backend.agent_endpoint("work"),
                         ("vsock", 4, AGENT_VSOCK_PORT))
        self.assertIsNone(self.backend.agent_endpoint("missing"))

    def test_remove_undefines_and_deletes_disk(self):
        self._create()
        self.backend.remove("personal")
        self.assertIsNone(self.backend.get("personal"))
        self.assertFalse((self.disks / "personal.qcow2").exists())


class BackendSelectionTests(unittest.TestCase):
    def test_default_is_fake(self):
        env = {k: v for k, v in os.environ.items() if k != "MINIQUIBES_BACKEND"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertIsInstance(default_backend(), FakeBackend)

    def test_env_selects_libvirt(self):
        fake = make_fake_libvirt()
        with mock.patch.dict(sys.modules, {"libvirt": fake}), \
                mock.patch.dict(os.environ, {"MINIQUIBES_BACKEND": "libvirt"}):
            self.assertIsInstance(default_backend(), LibvirtBackend)

    def test_unknown_backend_is_a_clean_error(self):
        with mock.patch.dict(os.environ, {"MINIQUIBES_BACKEND": "bogus"}):
            with self.assertRaises(QubesError):
                default_backend()

    def test_missing_libvirt_module_is_a_clean_error(self):
        # sys.modules['libvirt'] = None makes `import libvirt` raise ImportError
        with mock.patch.dict(sys.modules, {"libvirt": None}):
            with self.assertRaises(QubesError):
                LibvirtBackend()


if __name__ == "__main__":
    unittest.main()
