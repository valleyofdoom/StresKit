import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
from glob import glob

import requests

LOG_CLI = logging.getLogger("CLI")


def dl_file(url: str, outfile: str) -> int:
    if os.path.exists(outfile):
        LOG_CLI.info("cached binary %s found... skipping download", outfile)
        return 0

    LOG_CLI.info("downloading %s to %s", url, outfile)

    response = requests.get(url, timeout=5)

    if not response.ok:
        LOG_CLI.error(
            "response failed with status code %d - %s",
            response.status_code,
            response.text,
        )
        return 1

    with open(outfile, "wb") as fp:
        fp.write(response.content)

    return 0


def patch_linpack(bin_path: str) -> int:
    LOG_CLI.info("patching linpack binary located in %s", bin_path)

    with open(bin_path, "rb") as file:
        file_bytes = file.read()

    # convert bytes to hex as it's easier to work with
    file_hex_string = file_bytes.hex()

    # the implementation of this may need to change if more patching is required in the future
    matches = [
        (match.start(), match.group()) for match in re.finditer("e8f230", file_hex_string) if match.start() % 2 == 0
    ]

    LOG_CLI.debug("matches: %i", len(matches))

    # there should be one and only one match else quit
    if len(matches) != 1:
        return 1

    file_hex_string = file_hex_string.replace("e8f230", "b80100")
    # convert hex string back to bytes
    file_bytes = bytes.fromhex(file_hex_string)

    # save changes
    with open(bin_path, "wb") as file:
        file.write(file_bytes)

    return 0


def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image-version",
        metavar="<version>",
        type=str,
        help='specify the image version (e.g. 1.0.0 for v1.0.0). \
            version will be "UNKNOWN" if not specified',
        default="UNKNOWN",
    )

    parser.add_argument(
        "--clear-binary-cache",
        help="clears cache which forces a re-download of all binaries",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    logging.basicConfig(format="[%(name)s] %(levelname)s: %(message)s", level=logging.INFO)

    args = parse_args()

    build_directory = "/tmp/building"
    binary_cache = "/tmp/binary_cache"

    if args.clear_binary_cache:
        if os.path.exists(binary_cache):
            LOG_CLI.info("clearing binary cache")
            shutil.rmtree(binary_cache)
        else:
            LOG_CLI.info("binary cache folder not found... continuing")

    LOG_CLI.info("reading urls.json")

    with open("urls.json", encoding="utf-8") as fp:
        urls = json.load(fp)

    # make temp folder for building and cache
    LOG_CLI.info("creating temp folder %s", build_directory)
    os.makedirs(build_directory)
    os.makedirs(binary_cache, exist_ok=True)

    # ================================
    # Download and extract Porteus ISO
    # ================================

    # download porteus ISO
    porteus_iso = os.path.join(binary_cache, "Porteus.iso")

    if dl_file(urls["porteus"]["url"], porteus_iso) != 0:
        return 1

    # extract ISO contents to iso_contents folder
    iso_contents = os.path.join(build_directory, "iso_contents")

    try:
        subprocess.run(
            [
                "7z",
                "x",
                porteus_iso,
                f"-o{iso_contents}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to extract %s, %s", porteus_iso, e)
        return 1

    # ===========================
    # Modify Porteus ISO contents
    # ===========================

    # merge custom files with extracted iso
    LOG_CLI.info("merging custom files with extracted ISO")
    shutil.copytree("porteus", iso_contents, dirs_exist_ok=True)

    tools_folder = os.path.join(iso_contents, "porteus", "rootcopy", "usr", "local", "tools")
    LOG_CLI.debug("tools folder: %s", tools_folder)

    # =============
    # Setup Linpack
    # =============
    LOG_CLI.info("setting up Linpack")

    linpack_tgz = os.path.join(binary_cache, "linpack.tgz")

    if dl_file(urls["linpack"]["url"], linpack_tgz) != 0:
        return 1

    linpack_contents = os.path.join(build_directory, "linpack")

    with tarfile.open(linpack_tgz, "r:gz") as tar_file:
        tar_file.extractall(linpack_contents)

    # find benchmarks folder as the folder name (e.g. "benchmarks_2024.0") is dynamic
    benchmarks_folder = glob(os.path.join(linpack_contents, "benchmarks*"))

    LOG_CLI.debug("benchmarks folder glob result: %s", benchmarks_folder)

    if len(benchmarks_folder) != 1:
        return 1

    shutil.copy(
        os.path.join(
            benchmarks_folder[0],
            "linux",
            "share",
            "mkl",
            "benchmarks",
            "linpack",
            "xlinpack_xeon64",
        ),
        os.path.join(tools_folder, "linpack"),
    )

    # if patch_linpack(os.path.join(tools_folder, "linpack", "xlinpack_xeon64")) != 0:
    #     return 1

    # =============
    # Setup Prime95
    # =============
    LOG_CLI.info("setting up Prime95")

    prime95_tgz = os.path.join(binary_cache, "prime95.tgz")

    if dl_file(urls["prime95"]["url"], prime95_tgz) != 0:
        return 1

    with tarfile.open(prime95_tgz, "r:gz") as tar_file:
        tar_file.extractall(os.path.join(tools_folder, "prime95"))

    # ================
    # Setup y-cruncher
    # ================
    LOG_CLI.info("setting up y-cruncher")

    ycruncher_txz = os.path.join(binary_cache, "ycruncher.tar.xz")

    if dl_file(urls["y-cruncher"]["url"], ycruncher_txz) != 0:
        return 1

    ycruncher_contents = os.path.join(build_directory, "ycruncher")

    with tarfile.open(ycruncher_txz, "r:xz") as tar_file:
        tar_file.extractall(ycruncher_contents)

    # version name changes in folder name (e.g. "y-cruncher v0.8.3.9533")
    ycruncher_folder = glob(os.path.join(ycruncher_contents, "y-cruncher*-static"))

    LOG_CLI.debug("ycruncher folder folder glob result: %s", ycruncher_folder)

    if len(ycruncher_folder) != 1:
        return 1

    shutil.copytree(
        ycruncher_folder[0],
        os.path.join(tools_folder, "ycruncher"),
    )

    # ==================================
    # Setup Intel Memory Latency Checker
    # ==================================
    LOG_CLI.info("setting up Intel Memory Latency Checker")

    mlc_tgz = os.path.join(binary_cache, "mlc.tgz")

    if dl_file(urls["imlc"]["url"], mlc_tgz) != 0:
        return 1

    imlc_contents = os.path.join(build_directory, "imlc")

    with tarfile.open(mlc_tgz, "r:gz") as tar_file:
        tar_file.extractall(imlc_contents)

    shutil.move(os.path.join(imlc_contents, "Linux", "mlc"), tools_folder)

    # ==========================
    # Setup stressapptest (GSAT)
    # ==========================
    LOG_CLI.info("setting up stressapptest (GSAT)")

    stressapptest_zip = os.path.join(binary_cache, "stressapptest.zip")

    if dl_file(urls["stressapptest"]["url"], stressapptest_zip) != 0:
        return 1

    stressapptest_contents = os.path.join(build_directory, "stressapptest")

    try:
        subprocess.run(
            ["7z", "x", stressapptest_zip, f"-o{stressapptest_contents}"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to extract %s, %s", stressapptest_zip, e)
        return 1

    stressapptest_master = os.path.join(stressapptest_contents, "stressapptest-master")

    try:
        subprocess.run(
            ["bash", os.path.join(stressapptest_master, "configure")],
            check=True,
            cwd=stressapptest_master,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to execute configure script, %s", e)
        return 1

    try:
        subprocess.run(
            ["make"],
            check=True,
            cwd=stressapptest_master,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to run make %s", e)
        return 1

    shutil.move(os.path.join(stressapptest_master, "src", "stressapptest"), tools_folder)

    # ===========
    # Setup s-tui
    # ===========
    LOG_CLI.info("setting up s-tui")

    stui_zip = os.path.join(binary_cache, "s-tui.zip")

    if dl_file(urls["s-tui"]["url"], stui_zip) != 0:
        return 1

    stui_contents = os.path.join(build_directory, "s-tui")

    try:
        subprocess.run(
            ["pip", "install", "psutil", "urwid"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to install s-tui dependencies %s", e)
        return 1

    try:
        subprocess.run(
            ["7z", "x", stui_zip, f"-o{stui_contents}"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to extract %s, %s", stui_zip, e)
        return 1

    stui_master = os.path.join(stui_contents, "s-tui-master")

    try:
        subprocess.run(
            ["make"],
            check=True,
            cwd=stui_master,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to run make %s", e)

        # there is an undefined rule in the makefile which results in a non-zero exit code
        # but the build doesn't fail so there is no need to return

        # return 1

    shutil.move(os.path.join(stui_master, "s-tui"), tools_folder)

    # =================
    # Setup FIRESTARTER
    # =================
    LOG_CLI.info("setting up FIRESTARTER")

    firestarter_tgz = os.path.join(binary_cache, "firestarter.tgz")

    if dl_file(urls["firestarter"]["url"], firestarter_tgz) != 0:
        return 1

    firestarter_contents = os.path.join(build_directory, "firestarter")

    with tarfile.open(firestarter_tgz, "r:gz") as tar_file:
        tar_file.extractall(firestarter_contents)

    shutil.move(os.path.join(firestarter_contents, "FIRESTARTER"), tools_folder)

    # =====================
    # Pack ISO and clean up
    # =====================
    LOG_CLI.info("packing ISO and clean up")

    iso_fname = f"StresKit-v{args.image_version}-x86_64.iso"
    stresskit_iso = os.path.join(os.path.dirname(os.path.abspath(__file__)), iso_fname)

    try:
        subprocess.run(
            [
                "bash",
                os.path.join(iso_contents, "porteus", "make_iso.sh"),
                # output ISO path
                stresskit_iso,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        LOG_CLI.exception("failed to extract %s, %s", porteus_iso, e)
        return 1

    shutil.rmtree(build_directory)

    with open("sha256.txt", "w", encoding="utf-8") as fp:
        for file in (stresskit_iso,):
            sha256 = calculate_sha256(file)
            fname = os.path.basename(file)

            fp.write(f"{fname} {sha256}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
