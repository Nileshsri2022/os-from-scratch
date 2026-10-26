"""LibvirtBackend tests (ticket 02) — run against a fake `libvirt` module.

shortcut: the sandbox has no libvirt/KVM, so these tests verify XML
generation, state mapping, and call behaviour only. Real VM boot is verified
on the owner's machine (guide Step 6) before ticket 02 can close.
"""
import os
import re
import subprocess
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
        self._graphics_port = None      # real port revealed on start (like libvirt)
        self.stubborn = False          # True → shutdown() is ignored by the "guest"
        self.destroy_called = False

    def name(self):
        return self._name

    def state(self):
        return [self._state, 0]

    def create(self):
        self._state = VIR_DOMAIN_RUNNING
        if self._graphics_port is not None:
            self._xml = self._xml.replace("port='-1'", f"port='{self._graphics_port}'")

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
        self._next_graphics = 5900      # autoport allocation, like real libvirt
        self.networks = {"mq-net": object()}   # ticket 05: host has the net defined

    def networkLookupByName(self, name):
        if name not in self.networks:
            raise FakeLibvirtError(f"no network with name {name!r}")
        return self.networks[name]

    def defineXML(self, xml):
        name = re.search(r"<name>([^<]+)</name>", xml).group(1)
        # like real libvirt: an auto-assigned CID comes back in the domain XML
        xml = xml.replace("auto='yes'", f"auto='yes' address='{self._next_cid}'")
        self._next_cid += 1
        # like real libvirt: a stopped autoport domain reports port='-1'
        xml = xml.replace("autoport='yes'", "autoport='yes' port='-1'")
        dom = FakeDomain(self, name, xml)
        dom._graphics_port = self._next_graphics
        self._next_graphics += 1
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
        # every libvirt create now shells out to qemu-img (ticket 04 CoW):
        # default fake behaves like qemu-img (records argv, creates the clone)
        self.qemu_calls = []

        def fake_qemuimg(argv, **kw):
            self.qemu_calls.append(argv)
            Path(argv[-1]).write_bytes(b"CLONE")
            return types.SimpleNamespace(returncode=0)

        patcher = mock.patch("miniqubes.backends.subprocess.run", fake_qemuimg)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _create(self, name="personal", template="debian"):
        self.backend.create(Qube(name=name, template=template))

    def test_create_clones_with_a_backing_file_not_a_copy(self):
        self._create()
        self.assertEqual(self.qemu_calls, [[
            "qemu-img", "create", "-f", "qcow2",
            "-b", str(self.disks / "debian.qcow2"), "-F", "qcow2",
            str(self.disks / "personal.qcow2")]])
        self.assertEqual((self.disks / "personal.qcow2").read_bytes(), b"CLONE")
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

    def test_create_accepts_img_template_disk_as_raw_backing(self):
        # guide Step 3 downloads noble-server-cloudimg-amd64.img
        (self.disks / "noble.img").write_bytes(b"CLOUDIMG")
        self._create(name="work", template="noble")
        argv = self.qemu_calls[0]
        self.assertEqual(argv[argv.index("-F") + 1], "raw")
        self.assertEqual(argv[argv.index("-b") + 1],
                         str(self.disks / "noble.img"))

    def test_create_without_qemuimg_is_a_clean_error(self):
        def run(argv, **kw):
            raise FileNotFoundError("qemu-img")

        with mock.patch("miniqubes.backends.subprocess.run", run):
            with self.assertRaises(QubesError) as cm:
                self._create()
        self.assertIn("qemu-utils", str(cm.exception))
        self.assertEqual(self.conn.defined_xml, [])

    def test_create_qemuimg_failure_is_a_clean_error(self):
        argv_seen = []

        def run(argv, **kw):
            argv_seen.append(argv)
            raise subprocess.CalledProcessError(1, argv, stderr=b"boom: bad image")

        with mock.patch("miniqubes.backends.subprocess.run", run):
            with self.assertRaises(QubesError) as cm:
                self._create()
        self.assertIn("boom", str(cm.exception))
        self.assertEqual(self.conn.defined_xml, [])
        self.assertFalse((self.disks / "personal.qcow2").exists())

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

    def test_start_fails_clean_when_template_disk_missing(self):
        # a CoW clone reads its backing file at every boot — a vanished
        # template must be a clear error, not a cryptic qemu failure
        self._create()
        (self.disks / "debian.qcow2").unlink()
        with self.assertRaises(QubesError) as cm:
            self.backend.start("personal")
        self.assertIn("debian", str(cm.exception))
        self.assertEqual(self.conn.domains["mq-personal"].state()[0],
                         VIR_DOMAIN_SHUTOFF)   # dom.create() never ran

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

    def test_hostile_domain_xml_is_inert_not_parsed(self):
        # Mimosa L2: no general XML parser ever runs on domain XML (stdlib
        # ElementTree expands DTD entities) — a billion-laughs payload is
        # just inert text to the field regexes
        bomb = ("<?xml version='1.0'?><!DOCTYPE domain [<!ENTITY a 'boom'>"
                "<!ENTITY b '&a;&a;&a;&a;&a;&a;&a;&a;'>]>"
                "<domain><name>mq-bomb</name></domain>")
        self.conn.domains["mq-bomb"] = FakeDomain(self.conn, "mq-bomb", bomb)
        self.assertIsNone(self.backend.get("bomb").template)
        self.assertIsNone(self.backend.agent_endpoint("bomb"))
        self.assertEqual([q.name for q in self.backend.list()], ["bomb"])

    def test_create_attaches_mqnet_interface_with_isolation_filter(self):
        # ticket 05: every qube lands on the NAT network, behind the
        # qube↔qube-isolation nwfilter
        self._create()
        xml = self.conn.defined_xml[0]
        self.assertIn("<interface type='network'>", xml)
        self.assertIn("<source network='mq-net'/>", xml)
        self.assertIn("<filterref filter='mq-isolate'/>", xml)

    def test_create_defines_spice_graphics_localhost_only(self):
        # ticket 07: whole-desktop window, host-visible only on loopback.
        # Assert on the XML we generate — the fake conn (like real libvirt)
        # annotates a stopped autoport domain with port='-1' on the way in.
        xml = LibvirtBackend._domain_xml(Qube(name="personal", template="debian"),
                                         Path("d") / "personal.qcow2")
        self.assertIn("<graphics type='spice' autoport='yes' listen='127.0.0.1'/>", xml)
        self._create()                                     # and it reaches libvirt
        self.assertIn("spice", self.conn.defined_xml[0])

    def test_graphics_uri_reads_back_the_allocated_port(self):
        self._create()
        self.backend.start("personal")          # autoport is real only when running
        self.assertEqual(self.backend.graphics_uri("personal"),
                         ("spice", "127.0.0.1", 5900))
        self._create("work")
        self.backend.start("work")
        self.assertEqual(self.backend.graphics_uri("work"),
                         ("spice", "127.0.0.1", 5901))

    def test_graphics_uri_is_none_when_stopped_or_missing(self):
        self._create()                          # shutoff: XMLDesc reports port='-1'
        self.assertIsNone(self.backend.graphics_uri("personal"))
        self.assertIsNone(self.backend.graphics_uri("missing"))

    def test_create_without_mqnet_network_is_a_clean_error(self):
        # libvirt would refuse the define with a raw error; the guard must
        # fail before the qemu-img clone, leaving nothing behind
        self.conn.networks.clear()
        with self.assertRaises(QubesError) as cm:
            self._create()
        self.assertIn("mq-net", str(cm.exception))
        self.assertIn("net-define", str(cm.exception))
        self.assertEqual(self.conn.defined_xml, [])
        self.assertFalse((self.disks / "personal.qcow2").exists())
        self.assertEqual(self.qemu_calls, [])

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
