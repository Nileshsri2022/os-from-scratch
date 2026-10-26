#!/usr/bin/env bash
# make-template.sh — build one golden template image (ticket 04).
#
# Owner-machine tool (needs Linux with qemu-img [qemu-utils] and
# virt-customize [libguestfs-tools]). Recipe:
#   base cloud image → guest agent (ticket 03) → identity scrub → sealed
#   templates/<name>.qcow2
# AppQubes are instant CoW clones of it (LibvirtBackend.create:
# qemu-img create -f qcow2 -b <template> -F qcow2 <qube>.qcow2).
#
# Identity scrub before sealing (RE: qubes-linux-template-builder
# cleanup_image): clones must not share one machine-id, SSH host key, or
# history, or the compartments stop being distinguishable on the network.
#
# Usage: ./tools/make-template.sh <name> [base-image-url-or-path]
set -euo pipefail

name=${1:?usage: make-template.sh <name> [base-image-url-or-path]}
base=${2:-https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img}
repo="$(cd "$(dirname "$0")/.." && pwd)"
out="$repo/templates/$name.qcow2"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

for tool in qemu-img virt-customize; do
  command -v "$tool" >/dev/null ||
    { echo "missing tool: $tool (packages: qemu-utils, libguestfs-tools)" >&2; exit 1; }
done
mkdir -p "$repo/templates"

echo "==> base image: $base"
case "$base" in
  http*) curl -fL -o "$work/base.img" "$base" ;;
  *)     cp -- "$base" "$work/base.img" ;;
esac

echo "==> normalizing to templates/$name.qcow2"
qemu-img convert -f qcow2 -O qcow2 "$work/base.img" "$out"

echo "==> agent install + identity scrub + seal"
virt-customize -a "$out" \
  --mkdir /usr/local/lib/guest \
  --copy-in "$repo/guest/agent.py:/usr/local/lib/guest/" \
  --copy-in "$repo/miniqubes:/usr/local/lib/" \
  --copy-in "$repo/tools/mq-agent.service:/etc/systemd/system/" \
  --run-command 'systemctl enable mq-agent' \
  --run-command 'systemctl mask cloud-init.service cloud-config.service cloud-final.service' \
  --run-command 'truncate -s 0 /etc/machine-id' \
  --run-command 'rm -f /etc/ssh/ssh_host_*' \
  --run-command 'rm -f /root/.*history /home/*/.bash_history /root/.wget-hsts /home/*/.wget-hsts' \
  --run-command 'find /var/log -type f \( -name "*.log" -o -name "*.gz" \) -delete' \
  --run-command 'rm -rf /var/log/journal/*'

echo "==> sealed: $out"
echo "    verify with: qemu-img info $out   (format qcow2, no backing file)"
echo "    LibvirtBackend disks/ mein dekhta hai — golden ko wahan copy karo:"
echo "      mkdir -p ~/.local/share/miniqubes/disks"
echo "      cp $out ~/.local/share/miniqubes/disks/"
echo "    then: MINIQUIBES_BACKEND=libvirt python3 -m miniqubes create app --template $name"
