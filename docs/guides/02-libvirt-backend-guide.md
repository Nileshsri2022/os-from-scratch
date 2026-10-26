# Guide — Ticket 02: LibvirtBackend (real KVM qubes), step by step

> Ticket: `.scratch/os-from-scratch/issues/02-libvirt-backend.md` · Design ground:
> `docs/adr/0003-backend-interface-fake-first.md` · Ye guide **owner ki KVM/libvirt
> machine** par chalegi — sandbox mein `/dev/kvm` hai hi nahi, isliye ticket 02
> yahan close ho hi nahi sakta. Har step ke baad "Expected" likha hai taaki aap
> khud verify karke output bhej sako.

## Step 0 — Kya already ready hai (kuch naya design nahi karna)

| Cheez | Kahan | Status |
|---|---|---|
| Backend interface (7 methods: `create/start/stop/remove/get/list` + `agent_endpoint`) | `miniqubes/backends.py` | ✅ ticket 01 + 03 addendum |
| `FakeBackend` (JSON state file, bina KVM ke pura system chalta hai) | `miniqubes/backends.py` | ✅ |
| Guest agent vsock mode (`--vsock PORT`) | `guest/agent.py` | ✅ code ready, **real guest mein kabhi chala nahi** — ye ticket usi ko bhi verify karega |
| 36 unit tests (lifecycle, channel, policy, filecopy) | `tests/` | ✅ sab green |

**Ticket 02 ka matlab sirf itna hai:** `backends.py` mein ek nayi class
`LibvirtBackend` jo unhi 7 methods ko libvirt se jode, aur CLI mein
`MINIQUIBES_BACKEND=libvirt|fake` selection. Core, policy, channel, agent —
**kuch change nahi hona chahiye.** Agar change karna pade to wo design smell
hai; wahi ruk ke sochna (ADR-0003 ka pura point yahi tha).

## Step 1 — Owner machine par KVM + libvirt ready karo

Pehle hardware virtualization check:

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo     # 0 se bada number chahiye
ls -l /dev/kvm                          # file exist karni chahiye
```

Install (jo distro ho, usi wala block):

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients \
                 virtinst bridge-utils python3-libvirt

# Fedora
sudo dnf install @virtualization python3-libvirt
```

Phir user ko group mein daalo aur daemon chalao (group change ke liye
**logout/login zaroori** hai):

```bash
sudo usermod -aG libvirt,kvm $USER
sudo systemctl enable --now libvirtd
# logout → login ke baad:
virsh list --all          # Expected: khali table, error nahi
virt-host-validate        # Expected: QEMU line pe PASS (WARN chalega, FAIL nahi)
python3 -c "import libvirt; print(libvirt.getVersion())"   # Expected: ek number
```

vsock ke liye host module (permanent chahiye to `/etc/modules-load.d/vsock.conf`
mein `vhost_vsock` likh do):

```bash
sudo modprobe vhost_vsock
ls -l /dev/vsock          # Expected: file exist kare
```

## Step 2 — Repo lao, fake mode mein sab green confirm karo

```bash
git clone https://github.com/Nileshsri2022/os-from-scratch.git
cd os-from-scratch
git checkout arena/397029f8-os-from-scratch   # ya jo branch us samay active ho
python3 -m unittest discover -s tests          # Expected: Ran 36 tests ... OK
```

Ye pass hua to machine + repo dono sahi hain; ab asli kaam shuru.

## Step 3 — Ek guest disk image ready karo (ticket 04 se pehle ka jugaad)

Boot ke liye **ek ready qcow2 disk** chahiye. Templates/CoW wala proper system
ticket 04 hai — 02 ke liye sabse chhota rasta (ponytail): ek Ubuntu cloud image
download karke seedha istemal karo.

```bash
mkdir -p ~/.local/share/miniqubes/disks
cd ~/.local/share/miniqubes/disks
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
qemu-img info noble-server-cloudimg-amd64.img    # Expected: format: qcow2
```

(Doosra rasta: `virt-install` se ek chhoti VM bana ke uski disk yahan copy kar
do. Ticket 02 ke liye disk = bas ek file hai.)

## Step 4 — Code likho (TDD — pehle test red, phir code green)

Sandbox mein `libvirt` Python module nahi hai, isliye unit tests **fake libvirt
module** inject karke likhe jayenge (`sys.modules["libvirt"] = fake`) — XML
generation, state mapping aur call order test hoga; asli boot sirf Step 6 ki
checklist se verify hoga. Ye shortcut ticket ke Result mein label hoga.

### 4a. Pehle tests — `tests/test_libvirt_backend.py`

- Fake `libvirt`: `open()` → fake connection jisme `defineXML` domain banaye;
  domain ka state test control kare.
- Test cases:
  - `create` sahi naam (`mq-<qube>`) aur disk path ke saath XML define kare;
  - XML mein vsock device ho: `<vsock><cid auto='yes'/></vsock>` (libvirt khud
    CID dega — humein allocation ki kitab nahi rakhni);
  - template ka naam domain ke `<metadata>` mein jaaye (libvirt hi source of
    truth rahega, apni alag state file nahi);
  - `start/stop/remove/get/list` sahi domain calls karein; state mapping:
    libvirt RUNNING → `running`, baaki sab → `stopped`;
  - `agent_endpoint(name)` domain XML se CID padh ke
    `("vsock", cid, AGENT_VSOCK_PORT)` lautaaye;
  - backend selection: `MINIQUIBES_BACKEND` na ho → FakeBackend; `libvirt` ho →
    LibvirtBackend; aur libvirt module maujood na ho tab bhi baaki module
    import crash na kare (isiliye **lazy import**).

Chalao → **red** hona chahiye (`LibvirtBackend` abhi exist hi nahi karta).
Yahi sahi shuruaat hai.

### 4b. `LibvirtBackend` implement karo — sirf `miniqubes/backends.py` mein

Rules (ticket ke Design se):

- `import libvirt` **sirf isi file mein, lazy** (methods/`__init__` ke andar) —
  sandbox/tests kabhi libvirt na maangein.
- Domain XML (v1 fixed size: 1 vCPU, 1 GiB RAM — customization baad ki baat):

```xml
<domain type='kvm'>
  <name>mq-{name}</name>
  <metadata>
    <mq:template xmlns:mq='https://miniqubes.local/meta'>{template}</mq:template>
  </metadata>
  <memory unit='KiB'>1048576</memory>
  <vcpu>1</vcpu>
  <os><type arch='x86_64'>hvm</type></os>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <vsock model='virtio'><cid auto='yes'/></vsock>
    <console type='pty'/>
  </devices>
</domain>
```

- Method mapping (har method = 2–4 libvirt calls, isse zyada nahi):
  - `create(qube)` → template disk ko `disks/<name>.qcow2` copy (plain copy;
    CoW ticket 04 mein) + `defineXML(...)`
  - `start(name)` → `lookupByName("mq-"+name).create()`
  - `stop(name)` → pehle graceful `shutdown()`, ~10s poll, phir bhi na ruke to
    `destroy()` (graceful-then-force — ticket Verify ki shart)
  - `remove(name)` → `undefine()` + disk file delete
  - `get/list` → `listAllDomains()` mein se `mq-` wale chuno, `<metadata>` se
    template padho, `state()` map karo
  - `agent_endpoint(name)` → domain ka XML (`XMLDesc()`) parse karke
    `<cid address='N'/>` nikalo → `("vsock", N, AGENT_VSOCK_PORT)`; CID na mile
    to `None` (channel code isko already samajhta hai)
- Ek sab ke liye fixed guest vsock port rakho, jaise `AGENT_VSOCK_PORT = 27000`
  — har VM ka CID alag hota hai, isliye port takraayega nahi. (Fake wala
  per-qube TCP port isiliye tha kyunki wahan sab ek hi loopback par the.)

### 4c. CLI mein backend selection

```bash
MINIQUIBES_BACKEND=libvirt python3 -m miniqubes list   # libvirt wala rasta
python3 -m miniqubes list                              # default: fake (abhi bhi)
```

Default **fake hi rahega** jab tak ticket 02 owner machine par verify na ho
jaaye — Default badalna ticket close-out ka aakhri step hai, pehla nahi.

### 4d. Green karo

```bash
python3 -m unittest discover -s tests
# Expected: purane 36 + naye libvirt tests, sab OK — sandbox mein bina
# libvirt module ke bhi (fake module injection ki wajah se)
```

## Step 5 — Guest agent ko image ke andar daalo

Agent tabhi kaam karega jab wo VM ke andar chal raha ho. Ek baar image ko
boot karke (ya `virt-copy-in` se) ye daal do:

```bash
# guest ke andar (root):
mkdir -p /usr/local/lib/miniqubes
# host se copy: guest/agent.py + miniqubes/channel.py (agent ki zaroorat hai)
cat > /etc/systemd/system/mq-agent.service <<'EOF'
[Unit]
Description=MiniQubes guest agent (vsock)
After=multi-user.target
[Service]
ExecStart=/usr/bin/python3 /usr/local/lib/miniqubes/agent.py --vsock 27000
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now mq-agent
ss -tlnp | grep -i vsock || journalctl -u mq-agent -n 20   # agent zinda hai?
```

(Ticket 04 mein ye sab template banana ka hissa ban jayega — abhi haath se
ek baar karna ticket 02 ke liye kaafi hai.)

## Step 6 — Owner-machine verify checklist (yehi ticket ka asal exam hai)

Har line chalao aur output save karo — yehi transcript ticket ke Result mein
jayega:

```bash
export MINIQUIBES_BACKEND=libvirt
python3 -m miniqubes create personal --template noble-server-cloudimg-amd64
virsh list --all                 # Expected: mq-personal, shut off
python3 -m miniqubes start personal
virsh list --all                 # Expected: mq-personal, running
python3 -m miniqubes list        # Expected: personal  running
python3 -m miniqubes call personal ping
#   Expected: pong   ← 🎉 ticket 03 ka carried vsock item bhi yahi close hoga
python3 -m miniqubes stop personal     # Expected: graceful band (virsh: shut off)
python3 -m miniqubes remove personal
virsh list --all                 # Expected: mq-personal gayab + disk file delete
```

Bonus (time ho to): do qubes bana ke ticket 06 wala demo asli VMs par —
default mein `filecopy` deny, policy file ke baad allow, dono taraf sha256
same. Ye M2 ki taraf sabse bada saboot hoga.

## Step 7 — Close-out (hamara hamesha ka tareeka)

1. Transcript ko ticket 02 ke **Result** mein daalo; Steps check karo;
   `Status: done (<date>)`.
2. Ticket 03 ka bacha hua vsock checkbox bhi tick karo (wahi `pong` iska saboot hai).
3. `docs/STATUS.md` ki row 10 update karo; README mein backend default ka note.
4. Code-review pass (apna hi code dusri nazar se) → phir commit + push.
5. Tab — aur sirf tab — default backend `fake` → `libvirt` badalne ka faisla
   ADR addendum mein likho (ya env hi rakho; jo sach lage).

## Troubleshooting

| Dikkat | Matlab / ilaaj |
|---|---|
| `virsh`: permission denied / `Failed to connect socket` | Group membership ke baad logout/login nahi kiya; ya `systemctl status libvirtd` dekho |
| `error: Failed to start domain ... /dev/kvm: Permission denied` | User `kvm` group mein nahi (Step 1) |
| `No module named 'libvirt'` | `python3-libvirt` distro package lagao — pip wala rasta build deps maangta hai, mat padho usme |
| Domain XML validation error | `virt-xml-validate` se apna XML pehle check karo; aksar namespace wali line gadbad hoti hai |
| `mq call` → connection refused/timeout | Host par `vhost_vsock` module? Guest mein `mq-agent` service zinda hai? Guest kernel mein vsock support (Ubuntu cloud image mein hota hai) — teeno check karo |
| CID `None` aa raha hai | Domain define hone ke baad hi auto CID XML mein aata hai; `virsh dumpxml mq-personal \| grep -A1 vsock` se dekho |

## Labelled shortcuts (ponytail — chhupe hue nahi, likhe hue)

- **State polling** (libvirt events nahi) — CLI scale par kaafi hai.
- **CID = libvirt auto-assign**, hum sirf XML se padhte hain — apni allocation
  kitab nahi.
- **Disk = plain file copy** ticket 02 mein; CoW clones ticket 04 ka kaam hai.
- **1 vCPU / 1 GiB sab ke liye fixed** v1 mein — size customization tab, jab
  kisi ko sach mein chahiye ho.
- **Unit tests fake libvirt par** — XML/mapping test hota hai, asli boot nahi;
  asli saboot Step 6 ka transcript hai, test ka `OK` nahi.
