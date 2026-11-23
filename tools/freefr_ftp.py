#!/usr/bin/env python3
"""Publish the free.fr redirect stubs and clean the free.fr space, by FTP.

Credentials are read from ~/.netrc (never from the command line or the repo):
    machine ftpperso.free.fr login kaelig.castor password ********
    (chmod 600 ~/.netrc)

    python3 tools/freefr_ftp.py list                 # what is on the server
    python3 tools/freefr_ftp.py backup               # save server-only files locally (resumable)
    python3 tools/freefr_ftp.py upload [--yes]       # send dist/freefr/* (overwrite)
    python3 tools/freefr_ftp.py cleanup [--yes]      # delete everything except the stubs

The free.fr quota is 10 GB: when the space is over quota every upload is refused,
so run `cleanup --yes` BEFORE `upload --yes`. cleanup refuses to delete unless every
file has a verified local copy (same size) in the legacy folder or the backup.

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
        ftp = ftplib.FTP_TLS(HOST, timeout=60, encoding="latin-1")
        ftp.login(login, password)
        ftp.prot_p()
        print("connected (FTPS, encrypted)")
    except (ftplib.error_perm, OSError, EOFError):
        ftp = ftplib.FTP(HOST, timeout=60, encoding="latin-1")
        ftp.login(login, password)
        print("connected (plain FTP: the server does not offer TLS)")
    # free.fr stores some names as Latin-1 bytes; latin-1 maps every byte, so names
    # round-trip unchanged. local_name() turns them back into readable UTF-8.
    ftp.encoding = "latin-1"
    return ftp


def local_name(p):
    """Server path (latin-1 decoded bytes) -> local file name."""
    try:
        return p.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return p


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
        print(f"{n:6d} files {b / 1e6:9.1f} MB  {local_name(top)}")
    print(f"TOTAL {len(files)} files, {total / 1e9:.2f} GB")


def cmd_upload(ftp, yes):
    names = sorted(os.listdir(STUBS))
    for n in names:
        if yes:
            with open(os.path.join(STUBS, n), "rb") as fh:
                ftp.storbinary(f"STOR {n}", fh)
        print(("uploaded " if yes else "would upload ") + n)
    print(f"{len(names)} stubs {'uploaded' if yes else 'to upload'}")


def save_server_only(ftp, files, backup):
    """Download every server file not already in the local legacy copy (same name and size)."""
    def in_backup(p, s):
        for name in {local_name(p), p}:
            f = os.path.join(LEGACY, name)
            if os.path.isfile(f) and os.path.getsize(f) == s:
                return True
        return False
    todo = [(p, s) for p, s in files if not in_backup(p, s)]
    done = 0
    for p, s in todo:
        dest = os.path.join(backup, local_name(p))
        if os.path.isfile(dest) and os.path.getsize(dest) == s:
            continue  # already saved by a previous run
        if os.path.isfile(dest):  # same name in another letter case on a case-insensitive disk
            dest = case_copy(dest)
            if os.path.isfile(dest) and os.path.getsize(dest) == s:
                continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest + ".part", "wb") as fh:
            ftp.retrbinary(f"RETR {p}", fh.write)
        os.replace(dest + ".part", dest)
        done += 1
        if done % 100 == 0:
            print(f"  saved {done}/{len(todo)}", flush=True)
    return todo


def case_copy(path):
    stem, ext = os.path.splitext(path)
    return f"{stem}__case_copy{ext}"


def backup_dir():
    return os.path.join(PERSO, datetime.date.today().strftime("%Y%m%d") + "_kaeligcastorfreefr", "_server_only")


def cmd_backup(ftp):
    files = [(p, s) for p, d, s in walk(ftp) if not d]
    todo = save_server_only(ftp, files, backup_dir())
    print(f"{len(todo)} server-only files ({sum(s for _, s in todo) / 1e9:.2f} GB) saved in {backup_dir()}")


def cmd_cleanup(ftp, yes):
    keep = set(os.listdir(STUBS))
    items = list(walk(ftp))
    files = [(p, s) for p, d, s in items if not d and p not in keep]
    dirs = [p for p, d, _ in items if d]  # children listed before parents
    backup = backup_dir()

    def has_local_copy(p, s):
        for base in (LEGACY, backup):
            for name in {local_name(p), p}:
                f = os.path.join(base, name)
                for cand in (f, case_copy(f)):
                    if os.path.isfile(cand) and os.path.getsize(cand) == s:
                        return True
        return False

    # Safety net: save anything still missing, then refuse to delete if a copy is absent.
    save_server_only(ftp, [(p, s) for p, s in files if not has_local_copy(p, s)], backup) if yes else None
    missing = [(p, s) for p, s in files if not has_local_copy(p, s)]
    tops = {}
    for p, s in files:
        top = local_name(p.split("/")[0]) + ("/" if "/" in p else "")
        n, b = tops.get(top, (0, 0))
        tops[top] = (n + 1, b + s)
    print(f"{len(files)} files ({sum(s for _, s in files) / 1e9:.2f} GB) and {len(dirs)} folders to delete; {len(keep)} stubs kept")
    print(f"files without a verified local copy: {len(missing)}")
    for p, s in missing[:20]:
        print(f"  NO LOCAL COPY {local_name(p)} ({s} B)")
    if not yes:
        folders = sorted(t for t in tops if t.endswith("/"))
        loose = sorted(t for t in tops if not t.endswith("/"))
        print(f"folders ({len(folders)}): " + ", ".join(folders))
        print(f"loose files at the root: {len(loose)}")
        print("dry run: nothing changed (add --yes)")
        return
    if missing:
        sys.exit("ABORT: some files have no local copy; nothing deleted")
    refused = []
    n_files = n_dirs = 0
    for p, _ in files:
        try:
            ftp.delete(p)
            n_files += 1
        except ftplib.error_perm as e:  # e.g. free.fr's own read-only notice file
            refused.append(f"{local_name(p)}: {e}")
        if n_files and n_files % 500 == 0:
            print(f"  deleted {n_files}/{len(files)}", flush=True)
    for p in dirs:
        try:
            ftp.rmd(p)
            n_dirs += 1
        except ftplib.error_perm as e:
            refused.append(f"{local_name(p)}/: {e}")
    print(f"deleted {n_files} files and {n_dirs} folders; refused by the server: {len(refused)}")
    for r in refused[:20]:
        print("  kept", r)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "backup", "upload", "cleanup"):
        sys.exit(__doc__)
    yes = "--yes" in sys.argv
    if sys.argv[1] in ("upload", "cleanup") and not os.path.isdir(STUBS):
        sys.exit("dist/freefr/ missing: run python3 tools/build_freefr.py first")
    ftp = connect()
    try:
        {"list": lambda: cmd_list(ftp), "backup": lambda: cmd_backup(ftp), "upload": lambda: cmd_upload(ftp, yes),
         "cleanup": lambda: cmd_cleanup(ftp, yes)}[sys.argv[1]]()
    finally:
        ftp.quit()


if __name__ == "__main__":
    main()
