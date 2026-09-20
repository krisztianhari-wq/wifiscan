"""SQLite történet: futások, észlelések, ismert eszközök (címke, megbízható)."""
import json, os, sqlite3, time

DEFAULT_DB = os.path.expanduser("~/.wifiscan/history.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, ts TEXT, network TEXT, mode TEXT, n_hosts INT, n_new INT);
CREATE TABLE IF NOT EXISTS sightings(run_id INT, ip TEXT, mac TEXT, vendor TEXT, name TEXT, type TEXT, ports TEXT, services TEXT);
CREATE TABLE IF NOT EXISTS devices(mac TEXT PRIMARY KEY, label TEXT DEFAULT '', trusted INT DEFAULT 0,
  first_seen TEXT, last_seen TEXT, last_ip TEXT, vendor TEXT, seen_count INT DEFAULT 0);
CREATE INDEX IF NOT EXISTS s_run ON sightings(run_id);
CREATE TABLE IF NOT EXISTS networks(key TEXT PRIMARY KEY, label TEXT, ssid TEXT, gateway_ip TEXT, gateway_mac TEXT,
  gateway_vendor TEXT, subnet TEXT, first_seen TEXT, last_seen TEXT, run_count INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS device_networks(mac TEXT, network_key TEXT, first_seen TEXT, last_seen TEXT, seen_count INT DEFAULT 0,
  PRIMARY KEY(mac, network_key));
"""

MIGRATIONS = [
    "ALTER TABLE runs ADD COLUMN network_key TEXT",
]


class Store:
    def __init__(self, path=None):
        self.path = path or DEFAULT_DB
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        for m in MIGRATIONS:
            try:
                self.db.execute(m)
            except sqlite3.OperationalError:
                pass                                   # már megvan
        self._backfill()

    def _backfill(self):
        """Régi futások hely nélkül: alhálózat alapján kapnak helyet, az eszközök első látása is bekerül helyenként."""
        rows = self.db.execute("SELECT id, ts, network FROM runs WHERE network_key IS NULL ORDER BY id").fetchall()
        for r in rows:
            key = "net:" + r["network"]
            self._touch_network({"key": key, "ssid": "", "gateway_ip": "", "gateway_mac": "", "gateway_vendor": "",
                                 "subnet": r["network"], "default_label": r["network"]}, r["ts"])
            self.db.execute("UPDATE runs SET network_key=? WHERE id=?", (key, r["id"]))
            for s in self.db.execute("SELECT mac FROM sightings WHERE run_id=?", (r["id"],)).fetchall():
                self._touch_device_network(s["mac"], key, r["ts"])
        if rows:
            self.db.commit()

    def _touch_network(self, ident, ts):
        cur = self.db.cursor()
        row = cur.execute("SELECT key FROM networks WHERE key=?", (ident["key"],)).fetchone()
        if row is None and ident["key"].startswith("gw:"):
            # régi, alhálózat alapján azonosított hely ugyanezzel a subnettel -> átkulcsolás a gateway MAC-re
            legacy = "net:" + ident["subnet"]
            if cur.execute("SELECT key FROM networks WHERE key=?", (legacy,)).fetchone():
                for tbl, col in (("networks", "key"), ("runs", "network_key"), ("device_networks", "network_key")):
                    cur.execute(f"UPDATE {tbl} SET {col}=? WHERE {col}=?", (ident["key"], legacy))
                cur.execute("UPDATE networks SET gateway_mac=?, gateway_ip=?, gateway_vendor=? WHERE key=?",
                            (ident["gateway_mac"], ident["gateway_ip"], ident["gateway_vendor"], ident["key"]))
                row = cur.execute("SELECT key FROM networks WHERE key=?", (ident["key"],)).fetchone()
        if row is None:
            cur.execute("INSERT INTO networks(key,label,ssid,gateway_ip,gateway_mac,gateway_vendor,subnet,first_seen,last_seen,run_count) VALUES(?,?,?,?,?,?,?,?,?,1)",
                        (ident["key"], ident["default_label"], ident["ssid"], ident["gateway_ip"], ident["gateway_mac"],
                         ident["gateway_vendor"], ident["subnet"], ts, ts))
        else:
            cur.execute("UPDATE networks SET last_seen=?, run_count=run_count+1, subnet=?, gateway_ip=?, ssid=CASE WHEN ?<>'' THEN ? ELSE ssid END WHERE key=?",
                        (ts, ident["subnet"], ident["gateway_ip"], ident["ssid"], ident["ssid"], ident["key"]))
        return row is None

    def _touch_device_network(self, mac, key, ts):
        cur = self.db.cursor()
        row = cur.execute("SELECT mac FROM device_networks WHERE mac=? AND network_key=?", (mac, key)).fetchone()
        if row is None:
            cur.execute("INSERT INTO device_networks VALUES(?,?,?,?,1)", (mac, key, ts, ts))
        else:
            cur.execute("UPDATE device_networks SET last_seen=?, seen_count=seen_count+1 WHERE mac=? AND network_key=?", (ts, mac, key))
        return row is None

    def save_run(self, network, mode, hosts, ident=None):
        """Futás mentése. ident = engine.network_identity() eredménye; NEW = ezen a helyen először látott eszköz."""
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        ident = ident or {"key": "net:" + network, "ssid": "", "gateway_ip": "", "gateway_mac": "", "gateway_vendor": "",
                          "subnet": network, "default_label": network}
        new_location = self._touch_network(ident, ts)
        new = 0
        cur = self.db.cursor()
        for h in hosts:
            if len(h["mac"]) < 8:
                h["mac"] = "?@" + h["ip"]              # nincs ARP-válasz: IP alapján tartjuk nyilván
            row = cur.execute("SELECT mac FROM devices WHERE mac=?", (h["mac"],)).fetchone()
            if row is None:
                cur.execute("INSERT INTO devices(mac,first_seen,last_seen,last_ip,vendor,seen_count) VALUES(?,?,?,?,?,1)",
                            (h["mac"], ts, ts, h["ip"], h["vendor"]))
            else:
                cur.execute("UPDATE devices SET last_seen=?,last_ip=?,vendor=?,seen_count=seen_count+1 WHERE mac=?",
                            (ts, h["ip"], h["vendor"], h["mac"]))
            h["new"] = self._touch_device_network(h["mac"], ident["key"], ts) and not h.get("me")
            h["known_elsewhere"] = row is not None and h["new"]
            new += h["new"]
        cur.execute("INSERT INTO runs(ts,network,mode,n_hosts,n_new,network_key) VALUES(?,?,?,?,?,?)",
                    (ts, network, mode, len(hosts), new, ident["key"]))
        self.last_location_new = new_location
        rid = cur.lastrowid
        cur.executemany("INSERT INTO sightings VALUES(?,?,?,?,?,?,?,?)",
                        [(rid, h["ip"], h["mac"], h["vendor"], h.get("name", ""), h.get("type", ""),
                          json.dumps(h.get("ports", [])), h.get("services", "")) for h in hosts])
        self.db.commit()
        return rid, new

    def decorate(self, hosts):
        """Címke és megbízhatóság hozzáfűzése a devices táblából."""
        for h in hosts:
            r = self.db.execute("SELECT label,trusted,first_seen,seen_count FROM devices WHERE mac=?", (h["mac"],)).fetchone()
            h["label"] = r["label"] if r else ""
            h["trusted"] = bool(r["trusted"]) if r else False
            h["first_seen"] = r["first_seen"] if r else ""
            h["seen_count"] = r["seen_count"] if r else 0
        return hosts

    def update_services(self, run_id, services):
        for ip, svc in services.items():
            self.db.execute("UPDATE sightings SET services=? WHERE run_id=? AND ip=?", (svc, run_id, ip))
        self.db.commit()

    def runs(self, limit=40, network_key=None):
        q = "SELECT r.*, n.label AS location FROM runs r LEFT JOIN networks n ON n.key=r.network_key"
        args = []
        if network_key:
            q += " WHERE r.network_key=?"; args.append(network_key)
        q += " ORDER BY r.id DESC LIMIT ?"; args.append(limit)
        return [dict(r) for r in self.db.execute(q, args)]

    def networks(self):
        return [dict(r) for r in self.db.execute(
            "SELECT n.*, (SELECT COUNT(*) FROM device_networks d WHERE d.network_key=n.key) AS n_devices FROM networks n ORDER BY last_seen DESC")]

    def set_network_label(self, key, label):
        self.db.execute("UPDATE networks SET label=? WHERE key=?", (label, key)); self.db.commit()

    def network_of_run(self, run_id):
        r = self.db.execute("SELECT n.* FROM runs r JOIN networks n ON n.key=r.network_key WHERE r.id=?", (run_id,)).fetchone()
        return dict(r) if r else None

    def run_hosts(self, run_id):
        rows = [dict(r) for r in self.db.execute("SELECT * FROM sightings WHERE run_id=?", (run_id,))]
        for r in rows:
            r["ports"] = json.loads(r["ports"] or "[]")
        return self.decorate(rows)

    def devices(self, network_key=None):
        if network_key:
            return [dict(r) for r in self.db.execute(
                "SELECT d.*, dn.first_seen AS first_seen_here, dn.last_seen AS last_seen_here, dn.seen_count AS seen_here, n.label AS location "
                "FROM device_networks dn JOIN devices d ON d.mac=dn.mac JOIN networks n ON n.key=dn.network_key "
                "WHERE dn.network_key=? ORDER BY d.trusted, dn.last_seen DESC", (network_key,))]
        return [dict(r) for r in self.db.execute(
            "SELECT d.*, (SELECT GROUP_CONCAT(n.label, ' | ') FROM device_networks dn JOIN networks n ON n.key=dn.network_key WHERE dn.mac=d.mac) AS location "
            "FROM devices d ORDER BY d.trusted, d.last_seen DESC")]

    def set_device(self, mac, label=None, trusted=None):
        if label is not None:
            self.db.execute("UPDATE devices SET label=? WHERE mac=?", (label, mac))
        if trusted is not None:
            self.db.execute("UPDATE devices SET trusted=? WHERE mac=?", (1 if trusted else 0, mac))
        self.db.commit()

    def export(self, fmt="csv"):
        rows = self.devices()
        if fmt == "json":
            return json.dumps(rows, indent=2, ensure_ascii=False)
        import csv, io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["mac"])
        w.writeheader(); w.writerows(rows)
        return buf.getvalue()
