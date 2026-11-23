#!/usr/bin/env python3
"""Publish the free.fr redirect stubs and clean the free.fr space, by FTP.

Credentials are read from ~/.netrc (never from the command line or the repo):
    machine ftpperso.free.fr login kaelig.castor password ********
    (chmod 600 ~/.netrc)

    python3 tools/freefr_ftp.py list                 # what is on the server
    python3 tools/freefr_ftp.py upload [--yes]       # send dist/freefr/* (overwrite)
    python3 tools/freefr_ftp.py cleanup [--yes]      # delete everything except the stubs

Without --yes nothing is changed: the script prints what it would do.
Before deleting, `cleanup --yes` downloads every server file that is not
already in the local backup (same path, same size) into
../<YYYYMMDD>_kaeligcastorfreefr/_server_only/ so nothing is lost.
"""
import datetime
import ftplib
import netrc
import os
import sys

HOST = "ftpperso.free.fr"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STUBS = os.path.join(ROOT, "dist", "freefr")
PERSO = os.path.dirname(ROOT)
LEGACY = os.path.join(PERSO, "kaelig.castor.free.fr")


def connect():
    auth = netrc.netrc().authenticators(HOST)
    if not auth:
        sys.exit(f"No credentials for {HOST} in ~/.netrc")
    login, _, password = auth
    try:  # prefer an encrypted session when the server supports it
        ftp = ftplib.FTP_TLS(HOST, timeout=60)
        ftp.login(login, password)
        ftp.prot_p()
        print("connected (FTPS, encrypted)")
    except (ftplib.error_perm, OSError, EOFError):
        ftp = ftplib.FTP(HOST, timeout=60)
        ftp.login(login, password)
        print("connected (plain FTP: the server does not offer TLS)")
    ftp.encoding = "utf-8"
    return ftp


def walk(ftp, path=""):
    """Yield (path, is_dir, size) for everything under path."""
    try:
        entries = list(ftp.mlsd(path or ".", facts=["type", "size"]))
        for name, facts in entries:
            if name in (".", ".."):
                continue
            p = f"{path}/{name}" if path else name
            if facts.get("type") == "dir":
                yield from walk(ftp, p)
                yield p, True, 0
            elif facts.get("type") == "file":
                yield p, False, int(facts.get("size", 0))
    except ftplib.error_perm:
        # server without MLSD: fall back to NLST + probing with CWD
        for name in ftp.nlst(path or "."):
            base = name.rsplit("/", 1)[-1]
            if base in (".", ".."):
                continue
            p = f"{path}/{base}" if path else base
            try:
                ftp.cwd("/" + p)
                ftp.cwd("/")
                yield from walk(ftp, p)
                yield p, True, 0
            except ftplib.error_perm:
                try:
                    size = ftp.size(p) or 0
                except ftplib.error_perm:
                    size = 0
                yield p, False, size


def cmd_list(ftp):
    files = [(p, s) for p, d, s in walk(ftp) if not d]
    total = sum(s for _, s in files)
    tops = {}
    for p, s in files:
        top = p.split("/")[0] + ("/" if "/" in p else "")
        n, b = tops.get(top, (0, 0))
        tops[top] = (n + 1, b + s)
    for top, (n, b) in sorted(tops.items()):
        print(f"{n:6d} files {b / 1e6:9.1f} MB  {top}")
    print(f"TOTAL {len(files)} files, {total / 1e9:.2f} GB")


def cmd_upload(ftp, yes):
    names = sorted(os.listdir(STUBS))
    for n in names:
        if yes:
            with open(os.path.join(STUBS, n), "rb") as fh:
                ftp.storbinary(f"STOR {n}", fh)
        print(("uploaded " if yes else "would upload ") + n)
    print(f"{len(names)} stubs {'uploaded' if yes else 'to upload'}")


def cmd_cleanup(ftp, yes):
    keep = set(os.listdir(STUBS))
    items = list(walk(ftp))
    files = [(p, s) for p, d, s in items if not d and p not in keep]
    dirs = [p for p, d, _ in items if d]  # children listed before parents
    backup = os.path.join(PERSO, datetime.date.today().strftime("%Y%m%d") + "_kaeligcastorfreefr", "_server_only")
    to_save = [(p, s) for p, s in files
               if not (os.path.isfile(os.path.join(LEGACY, p)) and os.path.getsize(os.path.join(LEGACY, p)) == s)]
    print(f"{len(files)} files and {len(dirs)} folders to delete; {len(keep)} stubs kept")
    print(f"{len(to_save)} files exist only on the server -> saved first to {backup}")
    if not yes:
        for p, s in to_save[:50]:
            print(f"  would save   {p} ({s} B)")
        for p, _ in files[:30]:
            print(f"  would delete {p}")
        print("dry run: nothing changed (add --yes)")
        return
    for p, _ in to_save:
        dest = os.path.join(backup, p)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            ftp.retrbinary(f"RETR {p}", fh.write)
    print(f"saved {len(to_save)} server-only files")
    for p, _ in files:
        ftp.delete(p)
    for p in dirs:
        ftp.rmd(p)
    print(f"deleted {len(files)} files and {len(dirs)} folders")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "upload", "cleanup"):
        sys.exit(__doc__)
    yes = "--yes" in sys.argv
    if sys.argv[1] in ("upload", "cleanup") and not os.path.isdir(STUBS):
        sys.exit("dist/freefr/ missing: run python3 tools/build_freefr.py first")
    ftp = connect()
    try:
        {"list": lambda: cmd_list(ftp), "upload": lambda: cmd_upload(ftp, yes),
         "cleanup": lambda: cmd_cleanup(ftp, yes)}[sys.argv[1]]()
    finally:
        ftp.quit()


if __name__ == "__main__":
    main()
