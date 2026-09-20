#!/usr/bin/env python3
"""wifiscan engine – home network discovery (stdlib-only core, optional nmap).

CLI:
  wifiscan scan                 # discovery + vendor + name
  wifiscan scan --ports         # + quick port scan of common ports
  wifiscan scan --nmap          # + nmap -sV service detection
  wifiscan scan --json out.json # save result
"""
import argparse, concurrent.futures as cf, ipaddress, json, os, re, socket, subprocess, sys, time, urllib.request

OUI_URL = "https://standards-oui.ieee.org/oui/oui.csv"
OUI_CACHE = os.path.expanduser("~/.cache/wifiscan/oui.csv")

# Port -> tipp az eszköz típusára
PORT_HINTS = {
    22: "SSH", 23: "Telnet", 53: "DNS", 80: "HTTP", 443: "HTTPS", 445: "SMB",
    515: "Printer (LPD)", 548: "AFP (Mac/NAS)", 554: "RTSP (camera)",
    631: "IPP printer", 1883: "MQTT (IoT)", 1900: "UPnP", 3389: "RDP",
    5000: "Synology/UPnP", 5353: "mDNS", 7000: "AirPlay", 8008: "Chromecast",
    8009: "Chromecast", 8080: "HTTP-alt", 8443: "HTTPS-alt", 9100: "Printer (JetDirect)",
    32400: "Plex", 49152: "UPnP/Apple", 62078: "iPhone/iPad (lockdown)",
}
COMMON_PORTS = sorted(PORT_HINTS)


def default_interface():
    """A default route interfésze (WiFi nem mindig en0: Intel Mac-en gyakran en1)."""
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["route", "-n", "get", "default"], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"interface:\s*(\S+)", out)
        else:
            out = subprocess.check_output(["ip", "route", "show", "default"], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"\bdev\s+(\S+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def iface_network(iface):
    """IP + valódi netmaszk az interfészről (ifconfig / ip addr). Nagy hálózatot /22-re szűkítünk a saját IP körül."""
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["ifconfig", iface], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+) netmask 0x([0-9a-f]{8})", out)
            if not m:
                return None
            ip, mask = m.group(1), int(m.group(2), 16)
            prefix = bin(mask).count("1")
        else:
            out = subprocess.check_output(["ip", "-4", "-o", "addr", "show", iface], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", out)
            if not m:
                return None
            ip, prefix = m.group(1), int(m.group(2))
    except Exception:
        return None
    if prefix < 22:
        prefix = 22                                    # max 1022 cím, a saját IP körül
    return ip, ipaddress.ip_network(f"{ip}/{prefix}", strict=False)


def local_network():
    """Aktív interfész, saját IP és alhálózat. Sorrend: default route interfésze, majd en0/en1/wlan0/eth0."""
    cands = [i for i in [default_interface()] if i] + ["en0", "en1", "wlan0", "eth0"]
    seen = set()
    for iface in cands:
        if iface in seen or iface.startswith(("utun", "tun", "ipsec", "ppp", "lo")):
            continue
        seen.add(iface)
        r = iface_network(iface)
        if r:
            return iface, r[0], r[1]
    sys.exit("No active WiFi/Ethernet interface found.")


def route_interface(ip):
    """Melyik interfészen megy ki a forgalom az adott IP felé (macOS/BSD `route get`, Linux `ip route get`)."""
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(["route", "-n", "get", str(ip)], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"interface:\s*(\S+)", out)
        else:
            out = subprocess.check_output(["ip", "route", "get", str(ip)], text=True, stderr=subprocess.DEVNULL)
            m = re.search(r"\bdev\s+(\S+)", out)
        return m.group(1) if m else None
    except Exception:
        return None


def vpn_warning(iface, net):
    """Ha az alhálózat forgalma nem a WiFi/Ethernet interfészen megy (VPN elviszi), figyelmeztetés."""
    probe = list(net.hosts())[len(list(net.hosts())) // 2]
    via = route_interface(probe)
    if via and via != iface:
        return f"WARNING: {net} is routed via {via} (VPN?) instead of {iface} – the sweep will miss devices; disconnect the VPN or add a route"
    return ""


def _ping(ip, timeout_ms):
    if sys.platform == "darwin":
        # -i 0.2 + -t 1: a macOS ping egyébként +1 s-ot vár a -W után; így max ~0.7 s egy halott cím
        cmd = ["ping", "-c", "1", "-i", "0.2", "-W", str(timeout_ms), "-t", "1", str(ip)]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), str(ip)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ping_sweep(net, timeout_ms=600):
    """Egy menet minden címre (ARP-tábla feltöltése), aztán második menet csak a még hiányzókra."""
    hosts = list(net.hosts())
    with cf.ThreadPoolExecutor(128) as ex:
        list(ex.map(lambda ip: _ping(ip, timeout_ms), hosts))
    seen = set(arp_table(net))
    missing = [ip for ip in hosts if str(ip) not in seen]
    with cf.ThreadPoolExecutor(128) as ex:
        list(ex.map(lambda ip: _ping(ip, timeout_ms), missing))


def discover(net):
    """Teljes felderítés: ping sweep + mDNS/SSDP multicast, ARP-tábla pihentetés után. -> {ip: host}"""
    ping_sweep(net)
    mc = multicast_probe()
    time.sleep(1.5)
    hosts = arp_table(net)
    for ip, hint in mc.items():
        if ipaddress.ip_address(ip) not in net:
            continue
        h = hosts.setdefault(ip, {"ip": ip, "mac": "?"})
        h["hint"] = hint
    return hosts


def multicast_probe(timeout=1.5):
    """mDNS (5353) és SSDP (1900) multicast kérdés: a pingre nem válaszoló, de hirdető eszközök is ARP-bejegyzést kapnak.
    Visszaadja {ip: hint} – SSDP SERVER / mDNS név, ha kiolvasható."""
    found = {}
    ssdp = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n").encode()
    # mDNS: PTR kérdés _services._dns-sd._udp.local (id 0, QU bit)
    mdns = bytes.fromhex("000000000001000000000000") + b"\x09_services\x07_dns-sd\x04_udp\x05local\x00" + b"\x00\x0c\x80\x01"
    for addr, payload, port in ((("239.255.255.250", 1900), ssdp, 1900), (("224.0.0.251", 5353), mdns, 5353)):
        try:
            so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            so.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            so.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            so.settimeout(0.3)
            so.sendto(payload, addr); so.sendto(payload, addr)
            end = time.time() + timeout
            while time.time() < end:
                try:
                    data, (ip, _) = so.recvfrom(4096)
                except socket.timeout:
                    continue
                hint = ""
                if port == 1900:
                    m = re.search(rb"(?im)^SERVER:\s*(.+?)\r?$", data)
                    hint = m.group(1).decode(errors="ignore").strip() if m else "UPnP"
                else:
                    hint = "mDNS"
                found.setdefault(ip, hint)
            so.close()
        except OSError:
            pass
    return found


def arp_table(net):
    """arp -a kimenetből IP+MAC párok az alhálózaton."""
    out = subprocess.check_output(["arp", "-an"], text=True)      # -n: nincs reverse DNS, különben másodperceket vár
    hosts = {}
    for m in re.finditer(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-f:]+|\(incomplete\))", out):
        ip, mac = m.group(1), m.group(2)
        if mac == "(incomplete)" or ipaddress.ip_address(ip) not in net:
            continue
        if mac.lower().startswith(("ff:ff:ff", "01:00:5e", "33:33")) or ip == str(net.broadcast_address):
            continue                                   # broadcast / multicast nem eszköz
        # macOS rövid hexát ad (pl. a:1b:..), normalizáljuk
        mac = ":".join(p.zfill(2) for p in mac.split(":")).upper()
        hosts[ip] = {"ip": ip, "mac": mac}
    return hosts


NMAP_PREFIXES = ("/opt/homebrew/share/nmap/nmap-mac-prefixes", "/usr/local/share/nmap/nmap-mac-prefixes",
                 "/usr/share/nmap/nmap-mac-prefixes")
WIRESHARK_URL = "https://www.wireshark.org/download/automated/data/manuf"


def _download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (wifiscan)"})
    with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
        f.write(r.read())


def diagnose_empty(hosts, my_ip):
    """Ha csak a saját gép látszik: tipp a felhasználónak."""
    if len([h for h in hosts if h["ip"] != my_ip]) == 0:
        return ("Only this machine answered. Likely causes: client isolation on this WiFi (guest network), "
                "a VPN taking the route, or the network being larger than the scanned range.")
    return ""


def load_oui():
    """Gyártó a MAC első 3 bájtjából. Sorrend: nmap helyi lista, IEEE cache, Wireshark manuf."""
    oui = {}
    bundled_nmap()                                     # NMAPDIR beállítás, ha van beágyazott nmap
    paths = ([os.path.join(os.environ["NMAPDIR"], "nmap-mac-prefixes")] if os.environ.get("NMAPDIR") else []) + list(NMAP_PREFIXES)
    for path in paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line[:1] == "#" or not line.strip():
                        continue
                    k, _, v = line.strip().partition(" ")
                    oui[k.upper()] = v
            break
    stale = not os.path.exists(OUI_CACHE) or time.time() - os.path.getmtime(OUI_CACHE) > 30 * 86400
    if stale:
        os.makedirs(os.path.dirname(OUI_CACHE), exist_ok=True)
        for url in (OUI_URL, WIRESHARK_URL):
            try:
                _download(url, OUI_CACHE)
                break
            except Exception as e:
                print(f"[!] OUI download failed ({url.split('/')[2]}): {e}", file=sys.stderr)
    if os.path.exists(OUI_CACHE):
        with open(OUI_CACHE, encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("MA-L,"):                       # IEEE csv
                    parts = line.split(",", 3)
                    oui.setdefault(parts[1].strip().upper(), parts[2].strip().strip('"'))
                elif re.match(r"^[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}\t", line):  # wireshark manuf
                    cols = line.rstrip("\n").split("\t")
                    oui.setdefault(cols[0].replace(":", "").upper(), cols[2] if len(cols) > 2 and cols[2] else cols[1])
    if not oui:
        print("[!] No vendor database (neither nmap list nor download available)", file=sys.stderr)
    return oui


def vendor(mac, oui):
    if len(mac) < 8:
        return "unknown (no ARP reply)"
    prefix = mac.replace(":", "")[:6]
    second_nibble = int(mac[1], 16)
    if second_nibble & 0x2:
        return "(randomized MAC – phone/laptop private address)"
    return oui.get(prefix, "unknown")


def resolve_names(hosts, workers=32):
    """Reverse DNS párhuzamosan (soros híváskor 40 eszköznél másodpercek mennek el)."""
    with cf.ThreadPoolExecutor(workers) as ex:
        for h, name in zip(hosts, ex.map(lambda h: reverse_name(h["ip"]), hosts)):
            h["name"] = name
    return hosts


def reverse_name(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.gaierror):
        return ""


def scan_ports(ip, ports=COMMON_PORTS, timeout=0.5):
    open_ports = []
    def probe(port):
        with socket.socket() as s:
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                return port
    with cf.ThreadPoolExecutor(32) as ex:
        for r in ex.map(probe, ports):
            if r:
                open_ports.append(r)
    return sorted(open_ports)


def nmap_services(ip, sudo_pw=None, on_proc=None):
    """nmap -sV; sudo jelszóval -O OS-felismerés is. A jelszó csak stdin-en megy, sehol nem tárolódik."""
    nmap = shutil_which("nmap")
    if not nmap:
        return "nmap not installed"
    cmd = [nmap, "-sV", "-T4", "--top-ports", "100", ip]
    inp = None
    if sudo_pw:
        cmd = ["sudo", "-S", "-k", "-p", "", nmap, "-O", "--osscan-guess"] + cmd[1:]
        inp = sudo_pw + "\n"
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if on_proc:
            on_proc(proc)          # a hívó leállíthatja
        out, err = proc.communicate(inp, timeout=300)
        class R: pass
        r = R(); r.returncode, r.stdout, r.stderr = proc.returncode, out, err
        if proc.returncode in (-15, -9, 143):
            return "ABORTED"
        if sudo_pw and r.returncode != 0 and ("Sorry" in r.stderr or "password" in r.stderr.lower()):
            return "SUDO REJECTED · wrong password"
        keep = ("/tcp", "OS details", "Running", "Device type", "Aggressive OS guesses", "MAC Address", "No exact OS", "Host seems down")
        return "\n".join(l for l in r.stdout.splitlines() if any(k in l for k in keep)) or (r.stderr.strip() or "no open port in top-100")
    except Exception as e:
        return f"nmap error: {e}"


def bundled_nmap():
    """A csomagba ágyazott nmap (PyInstaller: vendor/nmap/bin/nmap[.exe]); beállítja az NMAPDIR-t is."""
    base = getattr(sys, "_MEIPASS", None) or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for root in (base, os.path.join(base, "vendor")):
        exe = os.path.join(root, "nmap", "bin", "nmap.exe" if os.name == "nt" else "nmap")
        if os.access(exe, os.X_OK):
            share = os.path.join(root, "nmap", "share", "nmap")
            if os.path.isdir(share):
                os.environ.setdefault("NMAPDIR", share)
            return exe
    return None


def shutil_which(cmd):
    """Beágyazott nmap → PATH → szokásos Homebrew/MacPorts helyek."""
    from shutil import which
    if cmd == "nmap":
        b = bundled_nmap()
        if b:
            return b
    found = which(cmd)
    if found:
        return found
    for d in ("/opt/homebrew/bin", "/usr/local/bin", "/opt/local/bin"):
        p = os.path.join(d, cmd)
        if os.access(p, os.X_OK):
            return p
    return None


VENDOR_RULES = [
    ("ubiquiti", "UniFi router / AP / switch"), ("routerboard", "MikroTik router"), ("mikrotik", "MikroTik router"),
    ("shenzhen bilian", "IoT / WiFi module"), ("murata", "IoT / embedded (Murata WiFi module)"), ("tp-link", "Router / AP"), ("asus", "Router / AP"),
    ("netgear", "Router / AP"), ("mikrotik", "Router"), ("zte", "Router / AP"),
    ("amazon", "Amazon Echo / Fire TV"), ("ring", "Ring camera / doorbell"), ("irobot", "Roomba robot vacuum"),
    ("nintendo", "Nintendo Switch"), ("sony interactive", "PlayStation"), ("microsoft", "Xbox / PC"),
    ("gree", "Gree air conditioner (WiFi module)"), ("tesla", "Tesla car"), ("shelly", "Shelly smart relay"),
    ("espressif", "IoT (ESP32/ESP8266)"), ("tuya", "IoT smart home"), ("sonoff", "IoT smart home"),
    ("lg electronics", "LG TV / appliance"), ("shenzhen sei", "Android TV box"), ("d&m", "Denon / Marantz receiver"),
    ("sonos", "Sonos speaker"), ("philips", "Philips Hue / TV"), ("google", "Google Nest / Chromecast"),
    ("raspberry", "Raspberry Pi"), ("synology", "Synology NAS"), ("qnap", "QNAP NAS"),
    ("hp inc", "HP printer / PC"), ("hewlett", "HP printer / PC"), ("canon", "Canon printer"),
    ("brother", "Brother printer"), ("epson", "Epson printer"), ("intel", "PC / laptop"),
    ("samsung", "Samsung phone / tablet / TV"), ("xiaomi", "Xiaomi phone / IoT"), ("huawei", "Huawei phone"),
    ("oneplus", "OnePlus phone"), ("apple", "Apple device"),
]
NAME_RULES = [
    ("iphone", "iPhone"), ("ipad", "iPad"), ("macbook", "MacBook"), ("imac", "iMac"), ("apple-tv", "Apple TV"),
    ("pixel", "Google Pixel phone"), ("galaxy-tab", "Samsung tablet"), ("galaxy", "Samsung phone"),
    ("-s2", "Samsung phone"), ("oneplus", "OnePlus phone"), ("a56", "Samsung phone"),
    ("tv-box", "Android TV box"), ("webos", "LG webOS TV"), ("tv", "TV"), ("laptop", "Laptop"),
    ("desktop", "PC"), ("shelly", "Shelly smart relay"), ("ring-", "Ring camera / doorbell"),
    ("irobot", "Roomba robot vacuum"), ("tesla", "Tesla car"), ("home-theater", "Home theater receiver"),
    ("unifi", "UniFi gateway"), ("u6", "UniFi AP"), ("us-8", "UniFi switch"), ("usw", "UniFi switch"),
    ("printer", "Printer"), ("nas", "NAS"), ("echo", "Amazon Echo"), ("chromecast", "Chromecast"),
]


def guess_type(h):
    v, ports, name = h["vendor"].lower(), h.get("ports", []), h.get("name", "").lower()
    hint = h.get("hint", "").lower()
    if "routeros" in hint or "mikrotik" in hint: return "MikroTik router"
    if "chromecast" in hint or "google" in hint and "upnp" in hint: return "Chromecast / Google"
    if "sonos" in hint: return "Sonos speaker"
    if "webos" in hint or "lg" in hint and "tv" in hint: return "LG webOS TV"
    if "roku" in hint: return "Roku"
    if "synology" in hint: return "Synology NAS"
    # 1. portok – a legbiztosabb jel
    if 62078 in ports: return "iPhone/iPad"
    if 8009 in ports: return "Chromecast / Android TV"
    if 9100 in ports or 631 in ports or 515 in ports: return "Printer"
    if 554 in ports: return "IP camera"
    if 7000 in ports: return "Apple TV / AirPlay"
    # 2. hostnév
    for key, label in NAME_RULES:
        if key in name:
            return label
    # 3. gyártó – szóhatáron illesztve ("ring" ne találjon a "Manufacturing"-ra)
    for key, label in VENDOR_RULES:
        if re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", v):
            return label
    # 4. portmintázat
    if 1883 in ports: return "IoT / smart home"
    if 445 in ports or 548 in ports or 5000 in ports: return "NAS / PC"
    if 22 in ports and 80 in ports: return "Linux device / router"
    if "randomiz" in v: return "Phone / laptop (private MAC)"
    return "?"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ports", action="store_true", help="gyors portscan a gyakori portokra")
    ap.add_argument("--nmap", action="store_true", help="nmap -sV szolgáltatás-felismerés")
    ap.add_argument("--json", metavar="FILE", help="eredmény mentése JSON-ba")
    a = ap.parse_args()

    iface, my_ip, net = local_network()
    print(f"[*] Interface: {iface}  my IP: {my_ip}  network: {net}")
    w = vpn_warning(iface, net)
    if w:
        print("[!] " + w, file=sys.stderr)
    print("[*] Ping sweep (populating ARP table)…")
    hosts = discover(net)
    print(f"[*] {len(hosts)} devices answered. Vendor and name lookup…")
    oui = load_oui()

    for h in hosts.values():
        h["vendor"] = vendor(h["mac"], oui)
        h["name"] = reverse_name(h["ip"])
        if a.ports or a.nmap:
            h["ports"] = scan_ports(h["ip"])
        if a.nmap:
            h["services"] = nmap_services(h["ip"])
        h["type"] = guess_type(h)

    print()
    print(f"{'IP':<16}{'MAC':<19}{'Vendor':<32}{'Type':<24}{'Name'}")
    print("-" * 110)
    for h in sorted(hosts.values(), key=lambda x: ipaddress.ip_address(x["ip"])):
        me = " (me)" if h["ip"] == my_ip else ""
        print(f"{h['ip']:<16}{h['mac']:<19}{h['vendor'][:30]:<32}{h['type']:<24}{h['name']}{me}")
        if h.get("ports"):
            print(f"{'':16}ports: " + ", ".join(f"{p} {PORT_HINTS.get(p,'')}".strip() for p in h["ports"]))
        if h.get("services"):
            for l in h["services"].splitlines():
                print(f"{'':16}  {l}")

    if a.json:
        with open(a.json, "w") as f:
            json.dump({"scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "network": str(net),
                       "hosts": list(hosts.values())}, f, indent=2, ensure_ascii=False)
        print(f"\n[*] Saved: {a.json}")


if __name__ == "__main__":
    main()
