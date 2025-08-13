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

sys.stdout.reconfigure(encoding="utf-8")

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95


# Check if the script is called from nzbget 18.0 or later
if not "NZBOP_EXTENSIONS" in os.environ:
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
    if not optname in os.environ:
        print(
            "[ERROR] Option %s is missing in NZBGet configuration. Please check script settings"
            % optname[6:]
        )
        sys.exit(POSTPROCESS_ERROR)

# If NZBGet Unpack setting isn't enabled, this script cannot work properly
if os.environ["NZBOP_UNPACK"] != "yes":
    print('[ERROR] You must enable option "Unpack" in NZBGet configuration, exiting')
    sys.exit(POSTPROCESS_ERROR)

sevenzipcmd = os.environ["NZBPO_SEVENZIPCMD"]
unrarcmd = os.environ["NZBPO_UNRARCMD"]
sevenzip_args = os.environ["NZBPO_SEVENZIPARGS"]
unrar_args = os.environ["NZBPO_UNRARARGS"]
waittime = os.environ["NZBPO_WAITTIME"]
deleteleftover = os.environ["NZBPO_DELETELEFTOVER"]

if sevenzipcmd == "":
    print(
        "[DETAIL] SevenZipCmd setting is blank. Using default NZBGet SevenZipCmd setting"
    )
    sevenzipcmd = os.environ["NZBOP_SEVENZIPCMD"]

if unrarcmd == "":
    print("[DETAIL] UnrarCmd setting is blank. Using default NZBGet UnrarCmd setting")
    unrarcmd = os.environ["NZBOP_UNRARCMD"]

# Check TOTALSTATUS
if os.environ["NZBPP_TOTALSTATUS"] != "SUCCESS":
    print("[WARNING] NZBGet download TOTALSTATUS is not SUCCESS, exiting")
    sys.exit(POSTPROCESS_NONE)

# Check if destination directory exists (important for reprocessing of history items)
if not os.path.isdir(os.environ["NZBPP_DIRECTORY"]):
    print(
        "[WARNING] Destination directory "
        + os.environ["NZBPP_DIRECTORY"]
        + " does not exist, exiting"
    )
    sys.exit(POSTPROCESS_NONE)

# Sleep (maybe)
if os.environ["NZBOP_UNPACKCLEANUPDISK"] == "yes":
    print(
        "[DETAIL] Sleeping "
        + waittime
        + " seconds to give NZBGet time to finish UnpackCleanupDisk action"
    )
    time.sleep(int(float(waittime)))

# Traverse download files to check for un-extracted zip files
print("[DETAIL] Searching for ZIP/RAR files")

sys.stdout.flush()


def get_full_path(dir, filename):
    return os.path.join(dir, filename)


def is_rar(filePath):
    _, fileExtension = os.path.splitext(filePath)
    return re.match(r"\.rar|\.r\d{2,3}$", fileExtension, re.IGNORECASE) is not None


def is_archive(filePath):
    _, fileExtension = os.path.splitext(filePath)
    return (
        re.match(r"\.zip|\.z\d{2,3}|\.rar|\.r\d{2,3}$", fileExtension, re.IGNORECASE)
        is not None
    )


status = 0
extract = 0
extracted = []
working_dir = os.environ["NZBPP_DIRECTORY"]


def unpack_recursively():
    global extract
    global status

    archives = list()
    for dirpath, _, filenames in os.walk(working_dir):
        paths = map(lambda filename: get_full_path(dirpath, filename), filenames)
        found_files = [
            file for file in paths if is_archive(file) and file not in extracted
        ]
        archives.extend(found_files)

    if len(archives) == 0:
        print("[INFO] No archive files found.")
        extract = 1
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
            print("[ERROR] Execution of sevenzip command failed: %s" % e)
            print("[ERROR] Unable to extract %s" % file)
            status = 1
            return

    unpack_recursively()


unpack_recursively()

sys.stdout.flush()

if extract == 1 and deleteleftover == "yes":
    print("[INFO] Deleting leftover zip files")
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
    sys.exit(POSTPROCESS_NONE)
