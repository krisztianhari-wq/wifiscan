# sadrobot wifiscan

*by **sadrobot** (Krisztián Hári)*

**EN** · Home-network device inventory: who is on the WiFi, vendor from the MAC address, device type, running
services (nmap), new-device alert per location. Python stdlib core, SQLite history, clean local web dashboard. English / Hungarian UI (toggle in the top bar).

**HU** · Otthoni hálózat eszközleltár: ki van a WiFi-n, gyártó a MAC-ből, eszköztípus, futó szolgáltatások
(nmap), új eszköz riasztás helyenként. Python stdlib mag, SQLite történet, letisztult helyi web dashboard. Angol / magyar felület (kapcsoló a felső sávban).

> Run it only on networks you own or are authorised to scan. · Csak saját vagy engedélyezett hálózaton futtasd.

![icon](assets/icon_256.png)

## Download / Letöltés

| Package | Needs | Contains nmap? |
|---|---|---|
| `WifiScan-macos-arm64.zip` → `WifiScan.app` | nothing (double-click) | **yes** (7.99x + data files) |
| `WifiScan-windows-x64.zip` | nothing; Npcap for `-O` | **yes** (nmap.org portable build) |
| `WifiScan-linux-x86_64.tar.gz` | nothing | **yes** (distro nmap + libs) |
| `wifiscan.pyz` (one file, any OS) | Python 3.9+, system nmap optional | no |
| `pip install .` → `wifiscan` command | Python 3.9+, system nmap optional | no |

The GUI opens at `http://127.0.0.1:8766/` (localhost only, token-protected API). Data: `~/.wifiscan/history.db`.

### macOS first launch / első indítás
The app is ad-hoc signed, not notarised: right-click → **Open**, or
`xattr -dr com.apple.quarantine WifiScan.app`.

## Usage / Használat

```bash
python3 -m wifiscan            # GUI  (or: wifiscan, ./dist/wifiscan.pyz, WifiScan.app)
python3 -m wifiscan scan       # terminal: discovery + vendor + name
python3 -m wifiscan scan --ports --nmap --json out.json
```

1. **Discover** — ping sweep of the /24, then `arp -a` → IP + MAC. Broadcast/multicast filtered.
2. **Identify** — vendor from IEEE OUI (nmap's `nmap-mac-prefixes` locally, IEEE / Wireshark download as fallback),
   reverse DNS name, randomized-MAC detection; device type from open-port patterns, hostname and vendor rules.
3. **Services** — quick TCP connect scan of common ports; **select rows → "Nmap on selected"** runs `nmap -sV`
   (with optional sudo password: `nmap -O` OS detection). The run is cancellable with **Stop**.
4. **History** — every run stored; a MAC seen for the first time is flagged **NEW**. Label / Trust per device,
   CSV / JSON export.

HU: 1. **Felderítés** ping sweep + ARP · 2. **Azonosítás** OUI gyártó, reverse DNS, randomizált MAC, típus-szabályok ·
3. **Szolgáltatások** portscan, kijelölt IP-kre `nmap -sV`, sudo jelszóval `-O` · 4. **Történet** új MAC = **NEW**, címke, Trust, export.

## Build

```bash
./build_pyz.sh                       # dist/wifiscan.pyz
./tools/bundle_nmap_macos.sh         # vendor/nmap  (Homebrew nmap made relocatable)   – macOS
./tools/bundle_nmap_windows.sh       # vendor/nmap  (nmap.org portable zip)             – Windows (Git Bash)
./tools/bundle_nmap_linux.sh         # vendor/nmap  (distro nmap + libs, patchelf)      – Linux
pip install pyinstaller && ./build_app.sh   # dist/app/WifiScan.*  + zip/tar.gz
python3 tools/make_icon.py assets/icon_1024.png   # regenerate the icon
```

## Layout
- `wifiscan/engine.py` — discovery, vendor lookup, port hints, type rules, nmap wrapper (bundled → PATH → Homebrew)
- `wifiscan/store.py` — SQLite history, devices, labels
- `wifiscan/gui.py` — local HTTP server + bilingual HTML/JS (127.0.0.1, token)
- `wifiscan/cli.py` — `wifiscan [gui|scan]`
- `tools/` — nmap bundlers, icon generator · `vendor/` — bundled nmap (generated, not committed)

Licenses: MIT (this project) · bundled components: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
