"""Check RAR/ZIP integrity using 7-Zip, including Windows UNC shares.

Usage: python archive_checker.py --config config.json
No archives are extracted or modified.
"""
import argparse
import csv
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def locate_7zip(configured):
    candidates = [configured, shutil.which("7z"), shutil.which("7zz"),
                  r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise FileNotFoundError("7-Zip executable not found. Set seven_zip_path in config.json.")


def find_archives(folder, recursive, extensions):
    """Yield archive paths; avoid following symlinked directories."""
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for name in files:
            if Path(name).suffix.lower() in extensions:
                yield os.path.join(root, name)
        if not recursive:
            break


def test_archive(seven_zip, path, timeout):
    # -p- prevents interactive password prompts; -y suppresses prompts.
    try:
        proc = subprocess.run(
            [seven_zip, "t", "-y", "-p-", "--", path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        output = proc.stdout or ""
        if proc.returncode == 0:
            return "OK", proc.returncode, output
        if "password" in output.lower() or "encrypted" in output.lower():
            return "PASSWORD_OR_ENCRYPTED", proc.returncode, output
        return "FAILED", proc.returncode, output
    except subprocess.TimeoutExpired as exc:
        return "TIMEOUT", "", str(exc)
    except OSError as exc:
        return "ERROR", "", str(exc)


def main():
    parser = argparse.ArgumentParser(description="Integrity-check .rar/.zip files with 7-Zip")
    app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    parser.add_argument("--config", default=None, help="Path to config.json (defaults to EXE folder)")
    args = parser.parse_args()
    config_path = Path(args.config).expanduser() if args.config else app_dir / "config.json"
    config_path = config_path.resolve()
    if not config_path.is_file():
        print(f"ERROR: Configuration file not found: {config_path}", file=sys.stderr)
        print("Place config.json next to ArchiveChecker.exe, or pass --config with its full path.", file=sys.stderr)
        return 2
    try:
        with config_path.open(encoding="utf-8-sig") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Cannot read configuration {config_path}: {exc}", file=sys.stderr)
        return 2
    print(f"Using configuration: {config_path}")
    seven_zip = locate_7zip(config.get("seven_zip_path", ""))
    report_dir = Path(config["report_folder"])
    report_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = report_dir / f"archive_check_{now}.csv"
    log_file = report_dir / f"archive_check_{now}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)])
    extensions = {e.lower() if e.startswith(".") else "." + e.lower()
                  for e in config.get("extensions", [".rar", ".zip"])}
    timeout = max(1, int(config.get("timeout_seconds_per_file", 3600)))
    counts = {"OK": 0, "FAILED": 0, "PASSWORD_OR_ENCRYPTED": 0,
              "TIMEOUT": 0, "ERROR": 0, "FOLDER_UNAVAILABLE": 0}
    with csv_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["checked_at", "archive_path", "size_bytes", "status", "7zip_exit_code", "details"])
        for folder in config["archive_folders"]:
            if not os.path.isdir(folder):
                counts["FOLDER_UNAVAILABLE"] += 1
                logging.error("Folder unavailable (path, network, or permission): %s", folder)
                writer.writerow([datetime.now().isoformat(timespec="seconds"), folder, "",
                                 "FOLDER_UNAVAILABLE", "", "Folder inaccessible or not found"])
                f.flush()
                continue
            logging.info("Scanning %s", folder)
            for archive in find_archives(folder, bool(config.get("recursive", True)), extensions):
                try:
                    size = os.path.getsize(archive)
                except OSError:
                    size = ""
                logging.info("Testing: %s", archive)
                status, code, details = test_archive(seven_zip, archive, timeout)
                counts[status] += 1
                logging.info("%s: %s", status, archive)
                writer.writerow([datetime.now().isoformat(timespec="seconds"), archive, size,
                                 status, code, details[-2000:].replace("\x00", "")])
                f.flush()
    logging.info("Finished. Results: %s", counts)
    logging.info("CSV report: %s", csv_file)
    logging.info("Log file: %s", log_file)
    return 1 if any(counts[k] for k in ["FAILED", "PASSWORD_OR_ENCRYPTED", "TIMEOUT", "ERROR", "FOLDER_UNAVAILABLE"]) else 0


if __name__ == "__main__":
    sys.exit(main())
