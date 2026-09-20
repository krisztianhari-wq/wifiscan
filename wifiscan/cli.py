"""wifiscan parancssor: `wifiscan` = GUI, `wifiscan scan [--ports|--nmap]` = terminál."""
import argparse, sys

from . import __version__


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wifiscan", description="sadrobot wifiscan – otthoni hálózat eszközleltár")
    ap.add_argument("--version", action="version", version="wifiscan " + __version__)
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("gui", help="webes felület (alapértelmezett)")
    g.add_argument("--port", type=int, default=8766)
    g.add_argument("--no-browser", action="store_true")
    g.add_argument("--db", help="SQLite fájl (alap: ~/.wifiscan/history.db)")
    g.add_argument("-v", "--verbose", action="store_true")
    sc = sub.add_parser("scan", help="terminálos scan")
    sc.add_argument("--ports", action="store_true")
    sc.add_argument("--nmap", action="store_true")
    sc.add_argument("--json", metavar="FILE")
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        from . import engine
        sys.argv = ["wifiscan"] + [f for f, on in (("--ports", a.ports), ("--nmap", a.nmap)) if on] + (["--json", a.json] if a.json else [])
        return engine.main()
    from .gui import serve
    port = getattr(a, "port", 8766); nb = getattr(a, "no_browser", False)
    return serve(port, not nb, getattr(a, "verbose", False), getattr(a, "db", None))


if __name__ == "__main__":
    sys.exit(main())
