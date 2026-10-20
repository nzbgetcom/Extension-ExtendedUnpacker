#!/usr/bin/env python3
#
# Copyright (C) 2024-2025 Denis <denis@nzbget.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with the program.  If not, see <https://www.gnu.org/licenses/>.
#

import sys
from os.path import dirname
import os
import subprocess
import unittest
import shutil
import json
import tarfile
import gzip

try:
    from main import (
        is_seven_zip_ext,
        is_rar_ext,
        is_rar_volume_ext,
        is_archive,
        is_rar,
    )
except ImportError:
    is_seven_zip_ext = None
    is_rar_ext = None
    is_rar_volume_ext = None
    is_archive = None
    is_rar = None



SUCCESS = 93
ERROR = 94
NONE = 95


sevenzip = os.environ.get("7z", "7z")
sevenzip_args = "e -aos"

unrar = os.environ.get("unrar", "unrar")
unrar_args = "e -idp -ai -o-"

root = dirname(__file__)

test_data_dir = root + "/test_data"
tmp_dir = root + "/tmp"

test_zips = ["test1.zip", "test2.zip", "test3.zip"]
test_partitioned_zips = ["test4.zip", "test4.z01", "test4.z02"]
test_rars = ["test1.rar", "test2.rar", "test3.rar"]
test_partitioned_rars = ["test4.r01", "test4.r02", "test4.r03"]
result_files = [tmp_dir + "/test1.txt", tmp_dir + "/test2.txt", tmp_dir + "/test3.txt"]
test_partitioned_result_files = ["test4.bin"]
test_partitioned_result_files = [tmp_dir + "/test4.bin"]

host = "127.0.0.1"
username = "TestUser"
password = "TestPassword"
port = "6789"


def get_python():
    if os.name == "nt":
        return "python"
    return "python3"


def run_script():
    sys.stdout.flush()
    proc = subprocess.Popen(
        [get_python(), root + "/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    out, err = proc.communicate()
    proc.pid
    ret_code = proc.returncode
    return (out.decode(), int(ret_code), err.decode())


def set_default_env():
    # NZBGet global options
    os.environ["NZBNA_EVENT"] = "FILE_DOWNLOADED"
    os.environ["NZBPP_DIRECTORY"] = tmp_dir
    os.environ["NZBOP_ARTICLECACHE"] = "8"
    os.environ["NZBPO_PASSACTION"] = "PASSACTION"
    os.environ["NZBOP_CONTROLPORT"] = port
    os.environ["NZBOP_CONTROLIP"] = host
    os.environ["NZBOP_CONTROLUSERNAME"] = username
    os.environ["NZBOP_CONTROLPASSWORD"] = password
    os.environ["NZBPR_PASSWORDDETECTOR_HASPASSWORD"] = "no"
    os.environ["NZBOP_EXTENSIONS"] = ""
    os.environ["NZBOP_UNPACK"] = "yes"
    os.environ["NZBPP_TOTALSTATUS"] = "SUCCESS"

    # script options
    os.environ["NZBNA_CATEGORY"] = "Movies"
    os.environ["NZBNA_DIRECTORY"] = tmp_dir
    os.environ["NZBNA_NZBNAME"] = "TestNZB"
    os.environ["NZBPR_FAKEDETECTOR_SORTED"] = "yes"
    os.environ["NZBOP_TEMPDIR"] = tmp_dir
    os.environ["NZBOP_SEVENZIPCMD"] = sevenzip
    os.environ["NZBPO_SEVENZIPCMD"] = sevenzip
    os.environ["NZBPO_SEVENZIPARGS"] = sevenzip_args
    os.environ["NZBOP_UNRARCMD"] = unrar
    os.environ["NZBPO_UNRARCMD"] = unrar
    os.environ["NZBPO_UNRARARGS"] = unrar_args
    os.environ["NZBPO_WAITTIME"] = "0"
    os.environ["NZBPO_DELETELEFTOVER"] = "no"
    os.environ["NZBOP_UNPACKCLEANUPDISK"] = "no"
    os.environ["NZBPO_MAXRECURSIONDEPTH"] = "10"
    os.environ["NZBPO_MAXTOTALARCHIVES"] = "100"


class Tests(unittest.TestCase):

    def test_sevenzip(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        set_default_env()

        shutil.copytree(
            test_data_dir,
            tmp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.r*"),
        )

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_unrar(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        set_default_env()

        shutil.copytree(
            test_data_dir,
            tmp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.z*"),
        )

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_sevenzip_with_empty_sevenzipcmd_option(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        set_default_env()
        os.environ["NZBPO_SEVENZIPCMD"] = ""

        shutil.copytree(
            test_data_dir,
            tmp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.r*"),
        )

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_unrar_with_empty_unrarcmd_option(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        set_default_env()
        os.environ["NZBPO_UNRARCMD"] = ""

        shutil.copytree(
            test_data_dir,
            tmp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.z*"),
        )

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_multiple_folders_zips(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        os.mkdir(tmp_dir)
        set_default_env()

        for index, zip in enumerate(test_zips):
            os.mkdir(str(f"{tmp_dir}/{index}"))
            shutil.copyfile(f"{test_data_dir}/{zip}", f"{tmp_dir}/{index}/{zip}")

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_multiple_folders_rars(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        os.mkdir(tmp_dir)
        set_default_env()

        for index, rar in enumerate(test_rars):
            os.mkdir(str(f"{tmp_dir}/{index}"))
            shutil.copyfile(f"{test_data_dir}/{rar}", f"{tmp_dir}/{index}/{rar}")

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in result_files:
            self.assertTrue(os.path.exists(file))

        shutil.rmtree(tmp_dir)

    def test_delete_leftovers_zips(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        os.mkdir(tmp_dir)
        set_default_env()
        os.environ["NZBPO_DELETELEFTOVER"] = "yes"

        for zip in test_partitioned_zips:
            shutil.copyfile(f"{test_data_dir}/{zip}", f"{tmp_dir}/{zip}")

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in test_partitioned_zips:
            self.assertFalse(os.path.exists(file))

        for file in test_partitioned_result_files:
            self.assertTrue(os.path.exists(file))
        shutil.rmtree(tmp_dir)

    def test_delete_leftovers_rars(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        os.mkdir(tmp_dir)
        set_default_env()
        os.environ["NZBPO_DELETELEFTOVER"] = "yes"

        for rar in test_partitioned_rars:
            shutil.copyfile(f"{test_data_dir}/{rar}", f"{tmp_dir}/{rar}")

        [_, code, _] = run_script()

        self.assertEqual(code, SUCCESS)

        for file in test_partitioned_rars:
            self.assertFalse(os.path.exists(file))

        for file in test_partitioned_result_files:
            self.assertTrue(os.path.exists(file))
        shutil.rmtree(tmp_dir)

    def test_manifest(self):
        with open(root + "/manifest.json", encoding="utf-8") as file:
            try:
                json.loads(file.read())
            except ValueError as e:
                self.fail("manifest.json is not valid.")

    def test_extension_helpers(self):
        self.assertIsNotNone(is_seven_zip_ext, "is_seven_zip_ext should be defined in main.py")
        self.assertIsNotNone(is_rar_ext, "is_rar_ext should be defined in main.py")
        self.assertIsNotNone(is_rar_volume_ext, "is_rar_volume_ext should be defined in main.py")

        # 7-Zip formats matching nzbget IsSevenZipExt
        seven_zip_formats = [
            ".7z", ".zip", ".tar", ".gz", ".bz", ".bz2", ".tgz", ".txz", ".xz",
            ".7Z", ".ZIP", ".TAR", ".GZ", ".BZ", ".BZ2", ".TGZ", ".TXZ", ".XZ"
        ]
        for ext in seven_zip_formats:
            self.assertTrue(is_seven_zip_ext(ext), f"Expected {ext} to be 7-zip ext")

        self.assertFalse(is_seven_zip_ext(".rar"))
        self.assertFalse(is_seven_zip_ext(".r00"))
        self.assertFalse(is_seven_zip_ext(".txt"))
        self.assertFalse(is_seven_zip_ext(""))

        # RAR format matching nzbget IsRarExt
        self.assertTrue(is_rar_ext(".rar"))
        self.assertTrue(is_rar_ext(".RAR"))
        self.assertFalse(is_rar_ext(".r00"))
        self.assertFalse(is_rar_ext(".zip"))
        self.assertFalse(is_rar_ext(""))

        # RAR volume format matching nzbget IsRarVolumeExt
        self.assertTrue(is_rar_volume_ext(".r00"))
        self.assertTrue(is_rar_volume_ext(".r99"))
        self.assertTrue(is_rar_volume_ext(".s00"))
        self.assertTrue(is_rar_volume_ext(".z00"))
        self.assertTrue(is_rar_volume_ext(".z99"))
        self.assertTrue(is_rar_volume_ext(".R00"))
        self.assertTrue(is_rar_volume_ext(".r100"))  # legacy 3-digit RAR volume

        self.assertFalse(is_rar_volume_ext(".rar"))
        self.assertFalse(is_rar_volume_ext(".000"))
        self.assertFalse(is_rar_volume_ext(".a00"))
        self.assertFalse(is_rar_volume_ext(".r0"))
        self.assertFalse(is_rar_volume_ext(".r0000"))
        self.assertFalse(is_rar_volume_ext(""))

    def test_is_archive_and_is_rar(self):
        self.assertIsNotNone(is_archive, "is_archive should be defined in main.py")
        self.assertIsNotNone(is_rar, "is_rar should be defined in main.py")

        archive_files = [
            "archive.7z", "archive.zip", "archive.tar", "archive.gz",
            "archive.bz", "archive.bz2", "archive.tgz", "archive.txz", "archive.xz",
            "archive.rar", "archive.r00", "archive.r01", "archive.s05", "archive.z01",
            "archive.r100"
        ]
        for name in archive_files:
            self.assertTrue(is_archive(name), f"Expected {name} to be archive")

        non_archives = ["file.txt", "video.mkv", "file.par2", "no_ext"]
        for name in non_archives:
            self.assertFalse(is_archive(name), f"Expected {name} not to be archive")

        # is_rar checks
        self.assertTrue(is_rar("archive.rar"))
        self.assertTrue(is_rar("archive.r00"))
        self.assertTrue(is_rar("archive.s01"))
        self.assertTrue(is_rar("archive.r100"))
        self.assertFalse(is_rar("archive.7z"))
        self.assertFalse(is_rar("archive.zip"))
        self.assertFalse(is_rar("archive.tar"))
        self.assertFalse(is_rar("archive.gz"))
        self.assertFalse(is_rar("archive.bz2"))
        self.assertFalse(is_rar("archive.xz"))

    def test_tar_gz_recursive_unpack(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        set_default_env()
        os.environ["NZBPO_DELETELEFTOVER"] = "yes"

        # Create nested archive: content.txt -> nested.tar -> nested.tar.gz
        inner_txt = os.path.join(tmp_dir, "content.txt")
        with open(inner_txt, "w") as f:
            f.write("hello from nested tar.gz")

        tar_path = os.path.join(tmp_dir, "nested.tar")
        with tarfile.open(tar_path, "w", format=tarfile.GNU_FORMAT) as tar:
            tar.add(inner_txt, arcname="content.txt")
        os.remove(inner_txt)

        tar_gz_path = os.path.join(tmp_dir, "nested.tar.gz")
        with open(tar_path, "rb") as f_in, gzip.open(tar_gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(tar_path)

        [out, code, err] = run_script()
        self.assertEqual(code, SUCCESS, f"Expected SUCCESS, got {code}. Out: {out}, Err: {err}")
        extracted_file = os.path.join(tmp_dir, "content.txt")
        self.assertTrue(os.path.exists(extracted_file), "content.txt should be extracted from nested tar.gz")
        self.assertFalse(os.path.exists(tar_gz_path), "nested.tar.gz should be deleted")
        self.assertFalse(os.path.exists(tar_path), "nested.tar should be deleted")

        shutil.rmtree(tmp_dir)

    def test_max_recursion_depth_protection(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        set_default_env()
        # Set recursion depth to 1
        os.environ["NZBPO_MAXRECURSIONDEPTH"] = "1"

        # Create a 2-level archive: content.txt in nested.tar in nested.tar.gz
        inner_txt = os.path.join(tmp_dir, "content.txt")
        with open(inner_txt, "w") as f:
            f.write("deep file")

        tar_path = os.path.join(tmp_dir, "nested.tar")
        with tarfile.open(tar_path, "w", format=tarfile.GNU_FORMAT) as tar:
            tar.add(inner_txt, arcname="content.txt")
        os.remove(inner_txt)

        tar_gz_path = os.path.join(tmp_dir, "nested.tar.gz")
        with open(tar_path, "rb") as f_in, gzip.open(tar_gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(tar_path)

        [out, code, err] = run_script()
        # With depth 1, the inner tar is reached at depth 2 which should be halted
        self.assertEqual(code, ERROR, f"Expected ERROR when max recursion depth is exceeded. Out: {out}")
        self.assertIn("recursion", out.lower())

        shutil.rmtree(tmp_dir)

    def test_7z_archive_unpack(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        set_default_env()
        os.environ["NZBPO_DELETELEFTOVER"] = "yes"

        inner_file = os.path.join(tmp_dir, "test7z.txt")
        with open(inner_file, "w") as f:
            f.write("content inside 7z")

        archive_7z = os.path.join(tmp_dir, "test.7z")
        subprocess.run([sevenzip, "a", archive_7z, inner_file], check=True, stdout=subprocess.DEVNULL)
        os.remove(inner_file)

        [out, code, err] = run_script()
        self.assertEqual(code, SUCCESS, f"Expected SUCCESS, got {code}. Out: {out}, Err: {err}")
        self.assertTrue(os.path.exists(inner_file), "test7z.txt should be extracted")
        self.assertFalse(os.path.exists(archive_7z), "test.7z should be deleted")

        shutil.rmtree(tmp_dir)

    def test_max_total_archives_protection(self):
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        set_default_env()
        # Limit total archives to 2
        os.environ["NZBPO_MAXTOTALARCHIVES"] = "2"

        # Copy 3 archives from test_data
        for zip_name in test_zips:
            shutil.copyfile(f"{test_data_dir}/{zip_name}", f"{tmp_dir}/{zip_name}")

        [out, code, err] = run_script()
        self.assertEqual(code, ERROR, f"Expected ERROR when max total archives is exceeded. Out: {out}")
        self.assertIn("total archives", out.lower())

        shutil.rmtree(tmp_dir)



if __name__ == "__main__":
    unittest.main()
