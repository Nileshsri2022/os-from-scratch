#!/usr/bin/env python3
"""Build an interactive connection graph of all QubesOS org repos.

Inputs : repos.json (GitHub API list), parents.tsv (fork -> parent full_name)
Outputs: index.html (single-file interactive canvas graph), ../qubesos-repos.md
Edge semantics are explicit in both outputs: family membership (architectural
grouping), fork lineage (GitHub truth), curated runtime links (documented
Qubes architecture), builder links (builderv2 builds every family).
"""
import json, colorsys, html, collections, pathlib

HERE = pathlib.Path(__file__).parent
repos = json.load(open(HERE / "repos.json"))
parents = {}
for line in open(HERE / "parents.tsv"):
    if "\t" in line:
        k, v = line.rstrip("\n").split("\t")
        parents[k] = v

# ---------- families (ordered: first match wins) ----------
FAMILIES = [  # key, label
    ("core", "Core system (dom0, qrexec, VM agents)"),
    ("gui", "GUI virtualization"),
    ("vmm", "Hypervisor / Xen / VMM"),
    ("linux", "Linux kernel & support"),
    ("templates", "VM templates"),
    ("desktop", "Desktop, X11 & audio"),
    ("apps", "Applications"),
    ("windows", "Windows support"),
    ("python", "Python libraries"),
    ("mgmt", "Management (Salt / Ansible)"),
    ("builder", "Builder, CI, testing & infra"),
    ("installer", "Installer & boot"),
    ("firmware", "Firmware & hardware"),
    ("security", "Security components"),
    ("docs", "Docs, website & community"),
    ("packages", "System packages & packaging forks"),
]
EXACT = {}
def put(fam, *names):
    for n in names: EXACT[n] = fam
put("docs", ".github","qubes-doc","qubes-offline-doc","qubes-issues","qubesos.github.io",
    "qubes-posts","qubes-hcl","qubes-attachment","qubes-roadmap","qubes-diagrams",
    "qubes-architecture","qubes-artwork","qubes-translated","training-materials")
put("security", "qubes-antievilmaid","qubes-secpack","qubes-tpm-extra","qubes-trousers-changer",
    "qubes-pecheck","panic_report","qubes-remote-support")
put("firmware", "qubes-fwupd","qubes-system76-firmware","qubes-intel-microcode","qubes-flashrom",
    "qubes-seabios","qubes-efitools","qubes-sbsigntools")
put("windows", "qvm-create-windows-qube")
put("installer", "qubes-pungi","qubes-pykickstart","qubes-blivet","qubes-initial-setup",
    "qubes-dracut","qubes-plymouth","qubes-grubby-dummy")
put("builder", "qubes-continuous-integration","openqa-tests-qubesos","tests-hw-setup",
    "qubes-g2g-report","qubes-infrastructure","qubes-infrastructure-mirrors")
put("mgmt", "qubes-salt","qubes-ansible","qubes-ansible-collections")
put("apps", "qubes-manager","qubes-video-companion","qubes-screenshot-helper",
    "qubes-disk-password-gui","qubes-notification-proxy","qubes-policy-control","qubes-dbus")
put("desktop", "qubes-xfce4-screensaver","qubes-xfdesktop","qubes-xscreensaver",
    "qubes-libwnck3","qubes-nautilus","qubes-gnome-software-plugin")
put("gui", "qubes-virtgpu-host")
put("vmm", "xen","xen-vhost-frontend","rust-vmm","rust-vmm-xen")
put("python", "old-qubes-python-u2flib-host")
PREFIX = [  # checked after EXACT
    ("qubes-core-", "core"), ("qubes-gui-", "gui"), ("qubes-vmm-", "vmm"),
    ("qubes-linux-", "linux"), ("qubes-template-", "templates"),
    ("qubes-desktop-", "desktop"), ("qubes-xorg-", "desktop"), ("qubes-alsa-", "desktop"),
    ("qubes-app-", "apps"), ("qubes-windows-", "windows"), ("qubes-python-", "python"),
    ("qubes-mgmt-", "mgmt"), ("qubes-builder", "builder"), ("build-", "builder"),
    ("updates-status", "builder"), ("qubes-installer-", "installer"),
    ("qubes-anaconda", "installer"), ("qubes-lorax", "installer"), ("qubes-grub2", "installer"),
    ("qubes-tpm2-", "security"),
]
def family(name):
    if name in EXACT: return EXACT[name]
    for pre, fam in PREFIX:
        if name.startswith(pre): return fam
    return "packages"

fam_keys = [k for k, _ in FAMILIES]
fam_label = dict(FAMILIES)
color = {}
for i, k in enumerate(fam_keys):
    r, g, b = colorsys.hsv_to_rgb(i / len(fam_keys), 0.62, 0.92)
    color[k] = "#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255))

# ---------- nodes ----------
nodes, edges = [], []
names = {r["name"] for r in repos}
for k in fam_keys:
    nodes.append({"id": "hub:" + k, "label": fam_label[k], "type": "hub", "family": k})
for r in repos:
    f = family(r["name"])
    nodes.append({"id": r["name"], "label": r["name"], "type": "repo", "family": f,
                  "desc": (r["description"] or "").strip(), "lang": r["language"] or "—",
                  "stars": r["stars"], "fork": r["fork"], "archived": r["archived"],
                  "url": r["url"], "updated": r["updated"][:10]})
    edges.append({"s": r["name"], "t": "hub:" + f, "kind": "family"})
ext_seen = set()
for r in repos:
    if not r["fork"]: continue
    p = parents.get(r["name"], "?")
    if p == "?": continue
    if p.startswith("QubesOS/") and p.split("/")[1] in names:
        edges.append({"s": r["name"], "t": p.split("/")[1], "kind": "fork", "label": "forked from " + p})
    else:
        if p not in ext_seen:
            ext_seen.add(p)
            nodes.append({"id": "ext:" + p, "label": p, "type": "external", "family": "external",
                          "url": "https://github.com/" + p})
        edges.append({"s": r["name"], "t": "ext:" + p, "kind": "fork", "label": "forked from " + p})

# ---------- curated runtime links (documented Qubes architecture) ----------
CURATED = [
    ("qubes-core-admin", "qubes-core-qrexec", "qubesd controls VMs; qrexec is the inter-VM RPC fabric"),
    ("qubes-core-qrexec", "qubes-core-agent-linux", "qrexec services run inside Linux VMs"),
    ("qubes-core-admin", "qubes-core-admin-client", "Admin API client library"),
    ("qubes-core-admin", "qubes-vmm-xen", "dom0 manages Xen VMs (via libvirt)"),
    ("qubes-gui-daemon", "qubes-gui-agent-linux", "GUI protocol: dom0 daemon <-> VM agent"),
    ("qubes-manager", "qubes-core-admin-client", "Qubes Manager GUI talks to qubesd via Admin API"),
    ("qubes-core-agent-linux", "qubes-linux-kernel", "VM agent runs on the Qubes kernel"),
]
for a, b, lab in CURATED:
    if a in names and b in names:
        edges.append({"s": a, "t": b, "kind": "runtime", "label": lab})
# builder links: builderv2 builds components of every family
for k in fam_keys:
    edges.append({"s": "qubes-builderv2", "t": "hub:" + k, "kind": "builder"})

fam_counts = collections.Counter(n["family"] for n in nodes if n["type"] == "repo")
data = {"nodes": nodes, "edges": edges,
        "families": [{"key": k, "label": fam_label[k], "color": color[k], "n": fam_counts[k]} for k in fam_keys],
        "stats": {"total": len(repos), "originals": sum(not r["fork"] for r in repos),
                  "forks": sum(r["fork"] for r in repos), "archived": sum(r["archived"] for r in repos),
                  "external": len(ext_seen)}}
print("nodes:", len(nodes), "edges:", len(edges))
print({k: fam_counts[k] for k in fam_keys})

# ---------- index.html ----------
HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QubesOS — all 215 repos, connected</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;font:14px/1.45 system-ui,sans-serif;background:#0d1117;color:#e6edf3;overflow:hidden}
header{position:fixed;top:0;left:0;right:0;padding:10px 14px;background:rgba(13,17,23,.92);border-bottom:1px solid #30363d;z-index:5}
h1{font-size:17px;margin:0 0 2px} .sub{color:#8b949e;font-size:12.5px}
#controls{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin-top:8px}
#controls label{cursor:pointer;color:#c9d1d9;white-space:nowrap}
input[type=search]{background:#161b22;border:1px solid #30363d;color:#e6edf3;border-radius:6px;padding:5px 9px;min-width:220px}
button{background:#21262d;border:1px solid #30363d;color:#e6edf3;border-radius:6px;padding:5px 10px;cursor:pointer}
#legend{position:fixed;left:10px;bottom:10px;background:rgba(22,27,34,.94);border:1px solid #30363d;border-radius:8px;padding:8px 10px;max-height:46vh;overflow:auto;z-index:4;font-size:12px}
#legend div{padding:2px 4px;cursor:pointer;border-radius:4px}#legend div:hover{background:#21262d}
#legend .on{background:#1f6feb33;outline:1px solid #1f6feb}
.sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
#tip{position:fixed;pointer-events:none;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px;max-width:340px;display:none;z-index:6;font-size:12.5px}
#tip b{font-size:13.5px}.muted{color:#8b949e}
canvas{display:block;cursor:grab}canvas:active{cursor:grabbing}
#hint{position:fixed;right:10px;bottom:10px;color:#8b949e;font-size:12px;background:rgba(22,27,34,.9);padding:6px 9px;border-radius:6px;border:1px solid #30363d;z-index:4}
a{color:#58a6ff}
</style></head><body>
<header>
<h1>QubesOS on GitHub — all <span id="st-total"></span> public repos, connected</h1>
<div class="sub"><span id="st-line"></span> · Node size ≈ ⭐ · white ring = fork · faded = archived · ◆ = component family · ▦ gray = upstream outside the org · click a repo to open it on GitHub</div>
<div id="controls">
<input id="q" type="search" placeholder="Search repos… (Enter = jump to first match)">
<label><input type="checkbox" id="e-family" checked> family links</label>
<label><input type="checkbox" id="e-fork" checked> fork lineage</label>
<label><input type="checkbox" id="e-runtime" checked> runtime links</label>
<label><input type="checkbox" id="e-builder" checked> builder builds-all</label>
<label><input type="checkbox" id="opt-labels" checked> labels</label>
<label><input type="checkbox" id="opt-arch" checked> show archived</label>
<label><input type="checkbox" id="opt-ext" checked> show upstreams</label>
<button id="reset">Reset view</button>
</div></header>
<canvas id="cv"></canvas><div id="legend"></div><div id="tip"></div>
<div id="hint">drag = pan · wheel = zoom · drag a node to pin it · data: GitHub API, 2026-10-26</div>
<script>const DATA=__DATA__;</script>
<script>
const cv=document.getElementById('cv'),ctx=cv.getContext('2d'),tip=document.getElementById('tip');
let W,H,DPR; function size(){DPR=Math.min(devicePixelRatio||1,2);W=innerWidth;H=innerHeight;cv.width=W*DPR;cv.height=H*DPR;cv.style.width=W+'px';cv.style.height=H+'px';} size(); addEventListener('resize',size);
const famColor={},famLabel={}; DATA.families.forEach(f=>{famColor[f.key]=f.color;famLabel[f.key]=f.label});
famColor.external='#8b949e';
const N=new Map(); DATA.nodes.forEach(n=>N.set(n.id,Object.assign({},n)));
const hubs=DATA.families.map(f=>f.key); const R=Math.min(innerWidth,innerHeight)*0.34||320;
hubs.forEach((k,i)=>{const a=i/hubs.length*Math.PI*2-Math.PI/2,h=N.get('hub:'+k);h.hx=Math.cos(a)*R;h.hy=Math.sin(a)*R;h.x=h.hx;h.y=h.hy;h.vx=h.vy=0;h.r=17;});
N.forEach(n=>{ if(n.type==='repo'){const h=N.get('hub:'+n.family);n.x=h.hx+(Math.random()-.5)*180;n.y=h.hy+(Math.random()-.5)*180;n.vx=n.vy=0;n.r=Math.max(4,Math.min(13,4+Math.log10((n.stars||0)+1)*3));}
 if(n.type==='external'){n.x=(Math.random()-.5)*900;n.y=(Math.random()-.5)*700;n.vx=n.vy=0;n.r=6;} });
const E=DATA.edges.map(e=>({s:N.get(e.s),t:N.get(e.t),kind:e.kind,label:e.label})).filter(e=>e.s&&e.t);
N.forEach(n=>n.adj=new Set()); E.forEach(e=>{e.s.adj.add(e.t);e.t.adj.add(e.s);});
let view={x:0,y:0,k:0.85},hover=null,dragN=null,pan=null,focusFam=null,query='';
const show={family:1,fork:1,runtime:1,builder:1};
function nodeVisible(n){
 if(n.type==='repo'&&n.archived&&!document.getElementById('opt-arch').checked)return false;
 if(n.type==='external'&&!document.getElementById('opt-ext').checked)return false;
 if(focusFam&&n.type!=='external'&&n.family!==focusFam)return false;
 return true;}
function edgeVisible(e){ if(!show[e.kind])return false; if(e.kind==='fork'&&(e.t.type==='external')&&!document.getElementById('opt-ext').checked)return false; return nodeVisible(e.s)&&nodeVisible(e.t);}
const SPR={family:[.012,95],fork:[.02,150],runtime:[.03,240],builder:[.004,420]};
let alpha=1;
function tick(){
 const nodes=[...N.values()].filter(nodeVisible);
 for(let i=0;i<nodes.length;i++){const a=nodes[i];
  for(let j=i+1;j<nodes.length;j++){const b=nodes[j];let dx=a.x-b.x,dy=a.y-b.y;let d2=dx*dx+dy*dy;if(d2<1){dx=Math.random()-.5;dy=Math.random()-.5;d2=1;}
   const d=Math.sqrt(d2); if(d>520)continue; const f=2600/d2*alpha; const fx=dx/d*f,fy=dy/d*f; a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;}}
 E.forEach(e=>{ if(!edgeVisible(e))return; const [k,len]=SPR[e.kind]; let dx=e.t.x-e.s.x,dy=e.t.y-e.s.y; const d=Math.max(1,Math.hypot(dx,dy)); const f=(d-len)*k*alpha; const fx=dx/d*f,fy=dy/d*f; e.s.vx+=fx;e.s.vy+=fy;e.t.vx-=fx;e.t.vy-=fy;});
 nodes.forEach(n=>{ if(n===dragN)return;
  if(n.type==='hub'){n.vx+=(n.hx-n.x)*.02*alpha;n.vy+=(n.hy-n.y)*.02*alpha;}
  n.vx+= -n.x*.0006*alpha; n.vy+= -n.y*.0006*alpha;
  n.vx*=.82;n.vy*=.82;n.x+=n.vx;n.y+=n.vy;});
 alpha=Math.max(.12,alpha*.995);
}
function toScreen(n){return [ (n.x*view.k)+W/2+view.x, (n.y*view.k)+H/2+view.y ];}
function draw(){
 ctx.setTransform(DPR,0,0,DPR,0,0); ctx.clearRect(0,0,W,H);
 const labels=document.getElementById('opt-labels').checked;
 E.forEach(e=>{ if(!edgeVisible(e))return; const [x1,y1]=toScreen(e.s),[x2,y2]=toScreen(e.t);
  const hot=hover&&(e.s===hover||e.t===hover);
  ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);
  if(e.kind==='runtime'){ctx.strokeStyle=hot?'#fff':'rgba(255,255,255,.55)';ctx.lineWidth=hot?2.2:1.4;ctx.setLineDash([]);}
  else if(e.kind==='fork'){ctx.strokeStyle=hot?'#d2a8ff':'rgba(210,168,255,.4)';ctx.lineWidth=1.1;ctx.setLineDash([4,4]);}
  else if(e.kind==='builder'){ctx.strokeStyle='rgba(139,148,158,.13)';ctx.lineWidth=1;ctx.setLineDash([2,6]);}
  else {ctx.strokeStyle=hot?famColor[e.s.family]:hexA(famColor[e.s.family==='external'?'external':e.s.family],.16);ctx.lineWidth=hot?1.6:1;ctx.setLineDash([]);}
  ctx.stroke();ctx.setLineDash([]);});
 [...N.values()].filter(nodeVisible).forEach(n=>{ const [x,y]=toScreen(n); if(x<-60||y<-60||x>W+60||y>H+60)return;
  const col=famColor[n.family]||'#8b949e'; ctx.globalAlpha=(n.archived?.38:1);
  if(n.type==='hub'){ ctx.save();ctx.translate(x,y);ctx.rotate(Math.PI/4);ctx.fillStyle=col;ctx.strokeStyle='#fff';ctx.lineWidth=1.6;const s=n.r*view.k*.8+5;ctx.fillRect(-s/2,-s/2,s,s);ctx.strokeRect(-s/2,-s/2,s,s);ctx.restore();}
  else if(n.type==='external'){ ctx.fillStyle='#6e7681';const s=n.r*view.k+4;ctx.fillRect(x-s/2,y-s/2,s,s);}
  else { ctx.beginPath();ctx.arc(x,y,n.r*view.k*.9+1.5,0,7);ctx.fillStyle=col;ctx.fill(); if(n.fork){ctx.strokeStyle='rgba(255,255,255,.85)';ctx.lineWidth=1.2;ctx.stroke();} }
  if(query&&n.label.toLowerCase().includes(query)){ctx.beginPath();ctx.arc(x,y,(n.r*view.k)+7,0,7);ctx.strokeStyle='#f9e2af';ctx.lineWidth=2;ctx.stroke();}
  if(n===hover){ctx.beginPath();ctx.arc(x,y,(n.r*view.k)+5,0,7);ctx.strokeStyle='#fff';ctx.lineWidth=1.6;ctx.stroke();}
  ctx.globalAlpha=1;
  const showLabel = labels && (n.type==='hub' || n===hover || (view.k>1.25&&n.type==='repo') || (query&&n.label.toLowerCase().includes(query)));
  if(showLabel){ctx.font=(n.type==='hub'?'600 12.5px':'11.5px')+' system-ui';ctx.fillStyle=n.type==='hub'?'#fff':'#c9d1d9';ctx.strokeStyle='rgba(13,17,23,.85)';ctx.lineWidth=3.5;const t=n.label;ctx.strokeText(t,x+9,y+4);ctx.fillText(t,x+9,y+4);}
 });
}
function hexA(hex,a){const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);return `rgba(${r},${g},${b},${a})`;}
(function loop(){tick();draw();requestAnimationFrame(loop);})();
function pick(mx,my){ let best=null,bd=1e9; N.forEach(n=>{ if(!nodeVisible(n))return; const [x,y]=toScreen(n); const d=Math.hypot(x-mx,y-my); const rr=Math.max(10,n.r*view.k+4); if(d<rr&&d<bd){bd=d;best=n;} }); return best;}
cv.addEventListener('mousemove',ev=>{ const mx=ev.clientX,my=ev.clientY;
 if(pan){view.x+=mx-pan[0];view.y+=my-pan[1];pan=[mx,my];return;}
 if(dragN){dragN.x=(mx-W/2-view.x)/view.k;dragN.y=(my-H/2-view.y)/view.k;dragN.vx=dragN.vy=0;alpha=Math.max(alpha,.35);return;}
 hover=pick(mx,my); cv.style.cursor=hover?'pointer':'grab';
 if(hover){ let h='<b>'+esc(hover.label)+'</b>';
  if(hover.type==='repo')h+='<br><span class="muted">'+esc(famLabel[hover.family])+'</span>'+(hover.desc?'<br>'+esc(hover.desc):'')+'<br><span class="muted">⭐ '+hover.stars+' · '+esc(hover.lang)+(hover.fork?' · fork':'')+(hover.archived?' · ARCHIVED':'')+' · updated '+hover.updated+'</span>';
  else if(hover.type==='hub')h+='<br><span class="muted">component family — click legend name to isolate</span>';
  else h+='<br><span class="muted">upstream repo outside QubesOS org</span>';
  tip.innerHTML=h;tip.style.display='block';tip.style.left=Math.min(W-360,mx+14)+'px';tip.style.top=(my+14)+'px';
 } else tip.style.display='none';});
cv.addEventListener('mousedown',ev=>{ const n=pick(ev.clientX,ev.clientY); if(n){dragN=n;dragN.moved=false;} else pan=[ev.clientX,ev.clientY]; });
addEventListener('mouseup',ev=>{ if(dragN&&!dragN.moved&&dragN.url){ if(Math.hypot(ev.clientX-(dragN.sx||0),ev.clientY-(dragN.sy||0))>=0) window.open(dragN.url,'_blank'); } dragN=null;pan=null;});
cv.addEventListener('mousedown',ev=>{ if(dragN){dragN.sx=ev.clientX;dragN.sy=ev.clientY;} });
cv.addEventListener('mousemove',ev=>{ if(dragN&&(Math.abs(ev.clientX-dragN.sx)>4||Math.abs(ev.clientY-dragN.sy)>4))dragN.moved=true; });
cv.addEventListener('wheel',ev=>{ ev.preventDefault(); const f=ev.deltaY<0?1.12:.89; view.k=Math.max(.18,Math.min(4,view.k*f)); },{passive:false});
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
['family','fork','runtime','builder'].forEach(k=>document.getElementById('e-'+k).addEventListener('change',e=>{show[k]=e.target.checked?1:0;alpha=.7;}));
['opt-arch','opt-ext','opt-labels'].forEach(id=>document.getElementById(id).addEventListener('change',()=>{alpha=.7;}));
document.getElementById('reset').onclick=()=>{view={x:0,y:0,k:.85};focusFam=null;query='';document.getElementById('q').value='';markLegend();alpha=.8;};
const q=document.getElementById('q');
q.addEventListener('input',()=>{query=q.value.trim().toLowerCase();});
q.addEventListener('keydown',e=>{ if(e.key!=='Enter')return; const m=[...N.values()].find(n=>n.type==='repo'&&n.label.toLowerCase().includes(query)&&nodeVisible(n)); if(m){view.x=-m.x*view.k;view.y=-m.y*view.k;hover=m;} });
const lg=document.getElementById('legend');
function markLegend(){ lg.innerHTML='<div style="cursor:default" class="muted">COMPONENT FAMILIES (click = isolate)</div>'+DATA.families.map(f=>'<div data-f="'+f.key+'" class="'+(focusFam===f.key?'on':'')+'"><span class="sw" style="background:'+f.color+'"></span>'+esc(f.label)+' <span class="muted">'+f.n+'</span></div>').join('');
 lg.querySelectorAll('[data-f]').forEach(d=>d.onclick=()=>{focusFam=focusFam===d.dataset.f?null:d.dataset.f;markLegend();alpha=.8;});}
markLegend();
document.getElementById('st-total').textContent=DATA.stats.total;
document.getElementById('st-line').textContent=DATA.stats.originals+' original · '+DATA.stats.forks+' forks (of '+DATA.stats.external+' upstreams) · '+DATA.stats.archived+' archived · '+DATA.families.length+' component families';
</script></body></html>'''
(HERE / "index.html").write_text(HTML.replace("__DATA__", json.dumps(data)))

# ---------- summary markdown ----------
lang = collections.Counter(r["language"] or "(none — mostly packaging/meta)" for r in repos)
owners = collections.Counter(p.split("/")[0] for p in parents.values())
top = sorted(repos, key=lambda r: -r["stars"])[:12]
by_fam = {k: sorted([r for r in repos if family(r["name"]) == k], key=lambda r: -r["stars"]) for k in fam_keys}
def link(n): return "[%s](https://github.com/QubesOS/%s)" % (n, n)
md = []
md.append("# QubesOS GitHub org — all 215 repos, and how they connect\n")
md.append("**Answer: exactly 215 public repositories** (GitHub API, 2026-10-26) — "
          "%d original, %d forks, %d archived. Interactive graph: "
          "[qubesos/index.html](qubesos/index.html) (open it, or see the live preview). "
          "Data: [qubesos/repos.json](qubesos/repos.json) · regeneration: "
          "[qubesos/build_graph.py](qubesos/build_graph.py).\n" % (data["stats"]["originals"], data["stats"]["forks"], data["stats"]["archived"]))
md.append("## The 215, by component family\n")
md.append("| Family | Repos | Flagships (by ⭐) |\n|---|---:|---|")
for k in fam_keys:
    flags = ", ".join(link(r["name"]) for r in by_fam[k][:3])
    md.append("| %s | %d | %s |" % (fam_label[k], fam_counts[k], flags))
md.append("\nFamilies are derived from repo naming + role (Qubes builds the OS from named "
          "*components*); the full per-repo classification is in the graph data.\n")
md.append("## Languages\n\n| Language | Repos |\n|---|---:|")
for k, v in lang.most_common(): md.append("| %s | %d |" % (k, v))
md.append("\n(61 \"Makefile\" repos are packaging components — they mostly contain build recipes "
          "that fetch and package upstream software, which is why GitHub reports no real language.)\n")
md.append("## Most-starred repos\n\n| ⭐ | Repo |\n|---:|---|")
for r in top: md.append("| %d | %s |" % (r["stars"], link(r["name"])))
md.append("\n## The 45 forks — where they come from\n")
md.append("Fork parents by owner: " + ", ".join("`%s` ×%d" % (o, c) for o, c in owners.most_common(8)) + ". "
          "Most are **maintainer working forks** (Qubes components are developed in a maintainer's fork, "
          "then mirrored into the org) — not random forks. The heavyweight true upstreams: "
          "**xen ← xen-project/xen** (the hypervisor itself), **rust-vmm / rust-vmm-xen ← rust-vmm org**, "
          "**qubes-template-kicksecure ← Kicksecure**, **qubes-system76-firmware ← pop-os**.\n")
md.append("""## How the 215 actually connect

**1. Build-time: one builder, ~200 components.** Qubes OS is not one codebase — it is assembled
from components, and nearly every repo here is one component (or a packaging recipe for one).
[qubes-builderv2](https://github.com/QubesOS/qubes-builderv2) builds them all into RPM/deb
packages in dependency order; the `build-logs*`, `updates-status*` and
[qubes-continuous-integration](https://github.com/QubesOS/qubes-continuous-integration) repos are
the CI paper trail. In the graph these are the dotted "builder builds-all" links.

**2. Runtime: dom0 at the center.** On an installed system the hub is
[qubes-core-admin](https://github.com/QubesOS/qubes-core-admin) (`qubesd`, running in dom0 on top
of Xen — [qubes-vmm-xen](https://github.com/QubesOS/qubes-vmm-xen) / [xen](https://github.com/QubesOS/xen)).
Everything talks to it through the Admin API ([qubes-core-admin-client](https://github.com/QubesOS/qubes-core-admin-client);
[qubes-manager](https://github.com/QubesOS/qubes-manager) is the GUI on top). VMs talk to each
other and to dom0 over **qrexec** ([qubes-core-qrexec](https://github.com/QubesOS/qubes-core-qrexec)),
with the in-VM half living in [qubes-core-agent-linux](https://github.com/QubesOS/qubes-core-agent-linux)
(and its Windows counterpart). Windows on screen are fake-local: the **GUI protocol** pipes each
VM's windows to dom0 — [qubes-gui-daemon](https://github.com/QubesOS/qubes-gui-daemon) (dom0) ↔
[qubes-gui-agent-linux](https://github.com/QubesOS/qubes-gui-agent-linux) (VM). These are the
white "runtime links" in the graph.

**3. Templates & management.** AppVMs are clones of template roots built from `qubes-template-*`
(Fedora/Debian/Kicksecure…) on top of [qubes-linux-kernel](https://github.com/QubesOS/qubes-linux-kernel);
their configuration is pushed by Salt — the `qubes-mgmt-salt-*` formulas.

**4. Lineage.** The dashed purple links are GitHub fork parentage (§ above): how code
*entered* the org.

### Graph edge legend (what a line means — and doesn't)

| Edge | Meaning | Source |
|---|---|---|
| colored thin | repo belongs to that component family (hub = family) | naming + role classification |
| purple dashed | GitHub fork-of (→ org repo or external upstream) | GitHub API (`parent`) |
| white solid | documented runtime relationship | Qubes architecture, curated (7 links) |
| gray dotted | builderv2 builds this family | Qubes build system |

**Honest limit:** family links show *architectural grouping*, not code-level imports. A true
build-dependency graph (component A BuildRequires component B) would need parsing every
component's `.qubesbuilder`/spec files — 215 clones. Doable as a follow-up if you want it,
but not claimed here.
""")
(HERE.parent / "qubesos-repos.md").write_text("\n".join(md))
print("wrote index.html + ../qubesos-repos.md")
print("packages leftovers:", ", ".join(r["name"] for r in by_fam["packages"]))
