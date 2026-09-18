# Third-party components in the packaged app

The desktop bundles (`WifiScan.app`, `WifiScan.exe`, `WifiScan` Linux) ship unmodified
binaries of the following open-source software so that no separate installation is needed.
The `.pyz` and `pip` distributions do **not** include them and use the system `nmap` instead.

| Component | Version | License | Source |
|---|---|---|---|
| Nmap (+ nmap-services, nmap-os-db, nmap-mac-prefixes, NSE scripts) | 7.99x | Nmap Public Source License (NPSL) | https://nmap.org |
| OpenSSL (libssl, libcrypto) | 3.x | Apache-2.0 | https://openssl.org |
| libssh2 | 1.x | BSD-3-Clause | https://libssh2.org |
| PCRE2 | 10.x | BSD-3-Clause | https://pcre.org |
| liblinear | 2.x | BSD-3-Clause | https://www.csie.ntu.edu.tw/~cjlin/liblinear |
| Lua | 5.x | MIT | https://lua.org |
| Python runtime (PyInstaller bundle) | 3.9+ | PSF-2.0 | https://python.org |

The full Nmap license text is copied into the bundle as `nmap/LICENSE-nmap.txt`.
Nmap is a trademark of Nmap Software LLC; this project is not affiliated with it.
On macOS the bundled nmap is taken from Homebrew (`tools/bundle_nmap_macos.sh`),
on Windows from the official nmap.org zip, on Linux from the distribution package
(`tools/bundle_nmap_*.sh`). Raw-socket features (`-O`, SYN scan) still need root/admin;
on Windows they additionally need the Npcap driver, which cannot be bundled silently.
