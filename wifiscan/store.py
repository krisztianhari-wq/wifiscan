"""SQLite történet: futások, észlelések, ismert eszközök (címke, megbízható)."""
import json, os, sqlite3, time

DEFAULT_DB = os.path.expanduser("~/.wifiscan/history.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, ts TEXT, network TEXT, mode TEXT, n_hosts INT, n_new INT);
CREATE TABLE IF NOT EXISTS sightings(run_id INT, ip TEXT, mac TEXT, vendor TEXT, name TEXT, type TEXT, ports TEXT, services TEXT);
CREATE TABLE IF NOT EXISTS devices(mac TEXT PRIMARY KEY, label TEXT DEFAULT '', trusted INT DEFAULT 0,
  first_seen TEXT, last_seen TEXT, last_ip TEXT, vendor TEXT, seen_count INT DEFAULT 0);
CREATE INDEX IF NOT EXISTS s_run ON sightings(run_id);
"""


class Store:
    def __init__(self, path=None):
        self.path = path or DEFAULT_DB
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def save_run(self, network, mode, hosts):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        new = 0
        cur = self.db.cursor()
        for h in hosts:
            if len(h["mac"]) < 8:
                h["mac"] = "?@" + h["ip"]              # nincs ARP-válasz: IP alapján tartjuk nyilván
            row = cur.execute("SELECT mac FROM devices WHERE mac=?", (h["mac"],)).fetchone()
            if row is None:
                new += 1
                cur.execute("INSERT INTO devices(mac,first_seen,last_seen,last_ip,vendor,seen_count) VALUES(?,?,?,?,?,1)",
                            (h["mac"], ts, ts, h["ip"], h["vendor"]))
            else:
                cur.execute("UPDATE devices SET last_seen=?,last_ip=?,vendor=?,seen_count=seen_count+1 WHERE mac=?",
                            (ts, h["ip"], h["vendor"], h["mac"]))
            h["new"] = row is None
        cur.execute("INSERT INTO runs(ts,network,mode,n_hosts,n_new) VALUES(?,?,?,?,?)", (ts, network, mode, len(hosts), new))
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

    def runs(self, limit=40):
        return [dict(r) for r in self.db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

    def run_hosts(self, run_id):
        rows = [dict(r) for r in self.db.execute("SELECT * FROM sightings WHERE run_id=?", (run_id,))]
        for r in rows:
            r["ports"] = json.loads(r["ports"] or "[]")
        return self.decorate(rows)

    def devices(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM devices ORDER BY trusted, last_seen DESC")]

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
