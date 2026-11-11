#!/usr/bin/env python3
"""Build pinned, Vulkan-only ANGLE DLLs for the MediaPipe Windows SDK."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

from build import SDK, apply_source_patch, fetch


def gitiles_tree_sha256(path):
    # Gitiles regenerates tar/gzip containers. Verify the paths, entry types,
    # modes, symlink targets, and bytes independently of archive timestamps.
    result = hashlib.sha256()
    with tarfile.open(path, "r:gz") as archive:
        for member in sorted(archive, key=lambda entry: entry.name):
            result.update((json.dumps([member.name, member.type.decode(), member.mode,
                                       member.linkname, member.size]) + "\n").encode())
            if member.isfile():
                with archive.extractfile(member) as stream:
                    result.update(hashlib.file_digest(stream, "sha256").digest())
    return result.hexdigest()


def prepare(out):
    lock = json.loads((SDK / "angle-sources.json").read_text())
    downloads = out / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    source = out / "source"
    if source.exists():
        shutil.rmtree(source)
    source.mkdir()
    archive = fetch(downloads,
        f"https://codeload.github.com/google/angle/tar.gz/{lock['angle_commit']}",
        lock["angle_sha256"], "angle.tar.gz")
    subprocess.run(["tar", "-xzf", archive, "--strip-components=1", "-C", source], check=True)
    for path, dependency in lock["dependencies"].items():
        archive = fetch(downloads, dependency["url"], dependency["tree_sha256"],
                        "angle-" + path.replace("/", "_") + ".tar.gz",
                        digest=gitiles_tree_sha256)
        dest = source / path
        dest.mkdir(parents=True, exist_ok=True)
        subprocess.run(["tar", "-xzf", archive, "-C", dest], check=True)
    # The four DEPS GN arguments normally written by gclient; no checkout,
    # auto-update hooks, installer, or dependency discovery is needed here.
    (source / "build/config/gclient_args.gni").write_text(
        "checkout_angle_internal = false\ncheckout_angle_mesa = false\n"
        "checkout_angle_restricted_traces = false\ngenerate_location_tags = false\n")
    (source / "build/util/LASTCHANGE").write_text(
        "LASTCHANGE=" + lock["angle_commit"] + "\n")
    (source / "build/util/LASTCHANGE.committime").write_text("1750000000\n")
    gn_archive = fetch(downloads, lock["gn"]["windows-amd64"]["url"],
                       lock["gn"]["windows-amd64"]["sha256"], "gn-windows-amd64.zip")
    gn_dir = out / "gn"
    gn_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(gn_archive) as archive:
        archive.extractall(gn_dir)
    rc = fetch(downloads, lock["rc"]["url"], lock["rc"]["sha256"], "chromium-rc.exe")
    shutil.copyfile(rc, source / "build/toolchain/win/rc/win/rc.exe")
    apply_source_patch(source, SDK / "angle-windows.diff", out)
    return source, gn_dir / "gn.exe", lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch", choices=["x64", "arm64"], required=True)
    parser.add_argument("--compiler", required=True, type=Path,
                        help="LLVM-MinGW root, used to generate GNU import libraries")
    parser.add_argument("--clang", required=True, type=Path,
                        help="Clang installation with clang-cl and lld-link for ANGLE's GN build")
    parser.add_argument("--out", type=Path, default=Path("build-angle"))
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    vswhere = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft Visual Studio/Installer/vswhere.exe"
    component = {"x64": "x86.x64", "arm64": "ARM64"}[args.arch]
    installation = json.loads(subprocess.check_output([
        vswhere, "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools." + component, "-format", "json", "-utf8",
    ], encoding="utf-8"))[0]
    sdk = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10"
    out = args.out.resolve()
    source, gn, lock = prepare(out)
    build = source / "out/Release"
    build.mkdir(parents=True, exist_ok=True)
    gn_args = {
        "target_os": "win", "target_cpu": args.arch,
        "is_debug": False, "is_component_build": False,
        "is_clang": True, "clang_base_path": args.clang.resolve().as_posix(),
        "visual_studio_path": Path(installation["installationPath"]).as_posix(),
        "visual_studio_version": installation["installationVersion"].split(".")[0],
        "windows_sdk_path": sdk.as_posix(), "wdk_path": sdk.as_posix(),
        "windows_sdk_version": "10.0.26100.0",
        "clang_use_chrome_plugins": False, "use_custom_libcxx": False,
        "use_sysroot": False, "use_siso": False, "use_remoteexec": False,
        "symbol_level": 0, "treat_warnings_as_errors": False,
        "angle_build_tests": False, "build_angle_deqp_tests": False,
        "angle_enable_vulkan": True, "angle_enable_gl": False,
        "angle_libs_suffix": "_qigao_mp",
        "angle_use_custom_libvulkan": False,
        "angle_enable_d3d9": False, "angle_enable_d3d11": False,
        "angle_enable_metal": False, "angle_enable_wgpu": False,
        "angle_enable_null": False, "angle_enable_swiftshader": False,
        "angle_enable_vulkan_validation_layers": False,
        "angle_enable_vulkan_api_dump_layer": False,
        "angle_has_astc_encoder": False, "angle_has_frame_capture": False,
        "angle_has_histograms": False, "angle_has_rapidjson": False,
        "angle_enable_overlay": False, "angle_build_vulkan_system_info": False,
    }
    (build / "args.gn").write_text("\n".join(
        name + " = " + json.dumps(value) for name, value in gn_args.items()) + "\n")
    env = os.environ | {"DEPOT_TOOLS_WIN_TOOLCHAIN": "0",
                        "DEPOT_TOOLS_UPDATE": "0",
                        "GYP_MSVS_OVERRIDE_PATH": installation["installationPath"],
                        "GIT_CEILING_DIRECTORIES": str(source.parent)}
    subprocess.run([gn, "gen", build], cwd=source, env=env, check=True)
    subprocess.run(["ninja", "-C", build, f"-j{args.jobs}", "libEGL", "libGLESv2"],
                   cwd=source, env=env, check=True)
    prefix = out / "package"
    if prefix.exists():
        shutil.rmtree(prefix)
    (prefix / "bin").mkdir(parents=True)
    (prefix / "lib").mkdir()
    shutil.copytree(source / "include", prefix / "include")
    shutil.copytree(source / "third_party/vulkan-headers/src/include/vulkan",
                    prefix / "include/vulkan")
    # ANGLE exposes a C DLL ABI. MediaPipe and GDMP retain LLVM-MinGW's C++
    # ABI; no ANGLE C++ symbols or MSVC import libraries cross that boundary.
    dlltool = args.compiler.resolve() / "bin/llvm-dlltool.exe"
    machine = {"x64": "i386:x86-64", "arm64": "arm64"}[args.arch]
    for name in ("libEGL", "libGLESv2"):
        dll_name = name + "_qigao_mp.dll"
        shutil.copyfile(build / dll_name, prefix / "bin" / dll_name)
        definitions = source / "src" / name / (name + "_autogen.def")
        private_def = build / (name + "_qigao_mp.def")
        private_def.write_text(definitions.read_text().replace("LIBRARY " + name, "LIBRARY " + dll_name))
        subprocess.run([dlltool, "-m", machine, "-D", dll_name, "-d", private_def,
                        "-l", prefix / "lib" / (name + "_qigao_mp.lib")], check=True)
    notices = prefix / "licenses"
    notices.mkdir()
    for path in [".", *lock["dependencies"]]:
        dest = notices / ("ANGLE" if path == "." else path.replace("/", "_"))
        dest.mkdir()
        for entry in (source / path).iterdir():
            if entry.is_file() and entry.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")):
                shutil.copyfile(entry, dest / entry.name)
    (prefix / "manifest.json").write_text(json.dumps(
        {"commit": lock["angle_commit"], "arch": args.arch, "backend": "vulkan",
         "swiftshader": False}, indent=2) + "\n")
    print(prefix)


if __name__ == "__main__":
    main()
