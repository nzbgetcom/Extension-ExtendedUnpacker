#!/usr/bin/env python
#
# Unzip post-processing script for NZBGet
#
# Copyright (C) 2014 thorli <thor78@gmx.at>
# Copyright (C) 2024-2025 Denis <denis@nzbget.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import sys
import subprocess
import time
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95

SEVEN_ZIP_FORMATS = (
    ".7z",
    ".zip",
    ".tar",
    ".gz",
    ".bz",
    ".bz2",
    ".tgz",
    ".txz",
    ".xz",
)


def is_seven_zip_ext(ext):
    return ext.lower() in SEVEN_ZIP_FORMATS


def is_rar_ext(ext):
    return ext.lower() == ".rar"


def is_rar_volume_ext(ext):
    ext = ext.lower()
    # Matches .r00-.z99 (NZBGet FileTypes::IsRarVolumeExt) and legacy .r000-.r999
    if re.match(r"^\.r\d{2,3}$", ext):
        return True
    if len(ext) == 4 and ext[0] == ".":
        return "r" <= ext[1] <= "z" and ext[2:].isdigit()
    return False


def has_rar_signature(file_path):
    try:
        with open(file_path, "rb") as f:
            header = f.read(7)
            return header.startswith(b"Rar!\x1a\x07")
    except OSError:
        return False


def is_archive(file_path):
    _, ext = os.path.splitext(file_path)
    if is_seven_zip_ext(ext):
        return True
    if is_rar_ext(ext) or is_rar_volume_ext(ext):
        return True
    if re.match(r"^\.z\d{2,3}$", ext, re.IGNORECASE):
        return True
    return False


def is_rar(file_path):
    _, ext = os.path.splitext(file_path)
    if is_rar_ext(ext):
        return True
    # Disambiguate .z01, .z02: if it has RAR signature it's RAR volume, otherwise split zip (7z)
    if re.match(r"^\.z\d{2,3}$", ext, re.IGNORECASE):
        return has_rar_signature(file_path)
    if is_rar_volume_ext(ext):
        return True
    return False


def get_full_path(directory, filename):
    return os.path.join(directory, filename)


def main():
    # Check if the script is called from nzbget 18.0 or later
    if "NZBOP_EXTENSIONS" not in os.environ:
        print("[ERROR] This script requires NZBGet v18.0 or later")
        sys.exit(POSTPROCESS_ERROR)

    print("[INFO] Script successfully started - python " + str(sys.version_info))
    sys.stdout.flush()

    # Check nzbget.conf options
    required_options = (
        "NZBOP_UNRARCMD",
        "NZBOP_SEVENZIPCMD",
        "NZBPO_UNRARCMD",
        "NZBPO_UNRARARGS",
        "NZBPO_SEVENZIPCMD",
        "NZBPO_SEVENZIPARGS",
        "NZBPO_WAITTIME",
        "NZBPO_DELETELEFTOVER",
    )
    for optname in required_options:
        if optname not in os.environ:
            print(
                "[ERROR] Option %s is missing in NZBGet configuration. Please check script settings"
                % optname[6:]
            )
            sys.exit(POSTPROCESS_ERROR)

    # If NZBGet Unpack setting isn't enabled, this script cannot work properly
    if os.environ.get("NZBOP_UNPACK") != "yes":
        print('[ERROR] You must enable option "Unpack" in NZBGet configuration, exiting')
        sys.exit(POSTPROCESS_ERROR)

    sevenzipcmd = os.environ["NZBPO_SEVENZIPCMD"]
    unrarcmd = os.environ["NZBPO_UNRARCMD"]
    sevenzip_args = os.environ["NZBPO_SEVENZIPARGS"]
    unrar_args = os.environ["NZBPO_UNRARARGS"]
    waittime = os.environ["NZBPO_WAITTIME"]
    deleteleftover = os.environ["NZBPO_DELETELEFTOVER"]

    try:
        max_recursion_depth = int(os.environ.get("NZBPO_MAXRECURSIONDEPTH", "10"))
    except ValueError:
        max_recursion_depth = 10

    try:
        max_total_archives = int(os.environ.get("NZBPO_MAXTOTALARCHIVES", "100"))
    except ValueError:
        max_total_archives = 100

    if sevenzipcmd == "":
        print(
            "[DETAIL] SevenZipCmd setting is blank. Using default NZBGet SevenZipCmd setting"
        )
        sevenzipcmd = os.environ["NZBOP_SEVENZIPCMD"]

    if unrarcmd == "":
        print("[DETAIL] UnrarCmd setting is blank. Using default NZBGet UnrarCmd setting")
        unrarcmd = os.environ["NZBOP_UNRARCMD"]

    # Check TOTALSTATUS
    if os.environ.get("NZBPP_TOTALSTATUS") != "SUCCESS":
        print("[WARNING] NZBGet download TOTALSTATUS is not SUCCESS, exiting")
        sys.exit(POSTPROCESS_NONE)

    # Check if destination directory exists (important for reprocessing of history items)
    if not os.path.isdir(os.environ.get("NZBPP_DIRECTORY", "")):
        print(
            "[WARNING] Destination directory "
            + str(os.environ.get("NZBPP_DIRECTORY", ""))
            + " does not exist, exiting"
        )
        sys.exit(POSTPROCESS_NONE)

    # Sleep (maybe)
    if os.environ.get("NZBOP_UNPACKCLEANUPDISK") == "yes":
        print(
            "[DETAIL] Sleeping "
            + str(waittime)
            + " seconds to give NZBGet time to finish UnpackCleanupDisk action"
        )
        time.sleep(int(float(waittime)))

    # Traverse download files to check for un-extracted archives
    print("[DETAIL] Searching for archive files")
    sys.stdout.flush()

    status = 0
    extract = 0
    extracted = []
    working_dir = os.environ["NZBPP_DIRECTORY"]

    def unpack_recursively(depth=0):
        nonlocal extract
        nonlocal status

        if depth >= max_recursion_depth:
            print(
                f"[ERROR] Maximum recursion depth ({max_recursion_depth}) exceeded!"
            )
            status = 1
            return

        archives = []
        for dirpath, _, filenames in os.walk(working_dir):
            paths = map(lambda filename: get_full_path(dirpath, filename), filenames)
            found_files = [
                file for file in paths if is_archive(file) and file not in extracted
            ]
            archives.extend(found_files)

        if len(archives) == 0:
            if depth == 0:
                print("[INFO] No archive files found.")
            extract = 1
            return

        if len(extracted) + len(archives) > max_total_archives:
            print(
                f"[ERROR] Maximum total archives limit ({max_total_archives}) exceeded!"
            )
            status = 1
            return

        for file in archives:
            print("[INFO] Extracting %s" % file)
            sys.stdout.flush()

            if is_rar(file):
                cmd = f'"{unrarcmd}" {unrar_args} "{file}" "{working_dir}"'
            else:
                cmd = f'"{sevenzipcmd}" {sevenzip_args} "{file}" -o"{working_dir}"'

            print(f"[INFO] Executing command: {cmd}")

            try:
                retcode = subprocess.call(cmd, shell=True)
                if retcode == 0 or retcode == 10:
                    print("[INFO] Extract Successful")
                    extracted.append(file)
                    extract = 1
                else:
                    print("[ERROR] Extract failed, Returncode %d" % retcode)
                    status = 1
                    return
            except OSError as e:
                print("[ERROR] Execution of extract command failed: %s" % e)
                print("[ERROR] Unable to extract %s" % file)
                status = 1
                return

        unpack_recursively(depth + 1)

    unpack_recursively()
    sys.stdout.flush()

    if extract == 1 and deleteleftover == "yes":
        print("[INFO] Deleting leftover archive files")
        for file in extracted:
            print("[INFO] Deleting %s" % file)
            try:
                os.remove(file)
            except OSError as e:
                print("[ERROR] Delete failed: %s" % e)
                print("[ERROR] Unable to delete %s" % file)
                status = 1

    if status == 0:
        sys.exit(POSTPROCESS_SUCCESS)
    else:
        sys.exit(POSTPROCESS_ERROR)


if __name__ == "__main__":
    main()
