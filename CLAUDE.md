# sadrobot wifiscan – fejlesztői jegyzet

Otthoni hálózati eszközleltár: ki van a WiFi-n, milyen eszköz, milyen szolgáltatásokkal; előzmény helyszínenként. Python 3.9+ stdlib, helyi webes GUI (HU/EN) + CLI + asztali app beépített nmap-pel. Felhasználói leírás: README.md.

## Indítás és teszt
- `python3 -m wifiscan` (= GUI, 127.0.0.1:8766, böngészőt nyit), `python3 -m wifiscan scan [--ports] [--nmap] [--json out.json]` terminálban. Opciók: `gui --port --db --no-browser`. Előzmény-DB: `~/.wifiscan/history.db`.
- launch.json (`~/Claude_code/.claude/launch.json`): `wifiscan-gui` (port 8767, eldobható DB: `/tmp/wifiscan-dev.db`) és `wifiscan-live` (port 8768, valódi előzmény).
- Automatikus teszt nincs. Kézi teszt: GUI → szkennelés a saját hálózaton, ellenőrizd a helyszín-csoportosítást és a NEW jelölést.

## Felépítés
- `wifiscan/engine.py` – felderítés: valódi netmask + default-route interfész, kétkörös ping (macOS: `ping -c 1 -i 0.2 -W <ms> -t 1`), `arp -an` (a sima `arp -a` lassú rDNS-t csinál), mDNS/SSDP próba, alhálózat-jelöltek (interface / dhcp / route / arp); OUI-gyártó, típus-szabályok, nmap-wrapper (beépített → PATH → Homebrew; `-Pn`, mert a hostot már az ARP-ból ismerjük).
- `wifiscan/store.py` – SQLite: futások, észlelések, eszközök (címke, Trust). Helyszín-kulcs: `gw:<gateway MAC>`; a régi `net:<cidr>` kulcsok beolvadnak a gw-kulcsba. NEW helyszínenként.
- `wifiscan/gui.py` – helyi HTTP-szerver (127.0.0.1, token) + kétnyelvű HTML/JS; a motor szövegei angolok, a JS fordít. `wifiscan/cli.py` – `wifiscan [gui|scan]`.
- `tools/bundle_nmap_{macos,windows,linux}.sh` → `vendor/nmap` (generált, nem commitolt). macOS: a Homebrew nmap relokálhatóvá téve (`install_name_tool`, `NMAPDIR`). Windows: az nmap.org új verzióhoz csak setup.exe-t ad, a bundler 7-Zippel bontja ki, tartalék a 7.92-es portable zip. `tools/make_icon.py` – ikonok.

## Telepítés / kiadás
- Verzió: `wifiscan/__init__.py` `__version__` (jelenleg 0.3.0). Kiadás: /release skill; `v*` tag → `.github/workflows/release.yml` buildel macOS arm64 + x86_64 (macos-15-intel), Windows x64, Linux x86_64 appot beépített nmap-pel és a release-hez csatolja.
- Helyi build: `./build_pyz.sh` (`dist/wifiscan.pyz`); app: előbb `tools/bundle_nmap_<os>.sh`, majd `./build_app.sh` (PyInstaller; `PYINSTALLER=` env-vel más venv PyInstallere is használható). A `--add-data` abszolút utat kér, mert `--specpath build`.

## Döntések
1. Helyszín = gateway MAC, nem SSID: macOS 14+ helymeghatározási engedély nélkül az SSID `<redacted>`; névnek a legelső preferált WiFi-hálózat a tipp.
2. Arculat: sadrobot (kék „sr” ikon), levegős dashboard halványkék palettával, rendszer-betűkészlettel (nincs webfont), üveg topbar, 14 px-es kártyák. Filmes/retró téma (korábban Alien, majd Hackerman) a tulajdonos kérésére eltávolítva – témázott stílust csak rákérdezés után.
3. Beépített nmap, hogy a célgépen ne kelljen se Python, se nmap. Licencek: THIRD_PARTY_NOTICES.md.

## Buktatók
- VPN-en át routolt helyi alhálózatnál a sweep eszközöket hagy ki – a GUI figyelmeztet.
- A Windows/Linux nmap-bundlerek a CI-ben futnak, helyben nem tesztelt.
- Telefonok/IoT blokkolják az nmap saját host-felderítését → `-Pn`.
