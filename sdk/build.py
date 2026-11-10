#!/usr/bin/env python3
"""Build a relocatable MediaPipe Tasks C++ SDK with pinned dependencies."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

SDK = Path(__file__).resolve().parent
MEDIAPIPE_COMMIT = "80ae8afbd03465b0d6d9f9e874f8cacf093d23e9"
MEDIAPIPE_VERSION = "0.10.26"
OCV_VERSION = "0.1.0"
OCV_SHA = {
    "linux-x64": "01fe644d9869c2ed2f79e6078f8fbaece6725d2175bbf2806a62d689d34f8237",
    "linux-arm64": "16ced3247662a09c0f1fa10832d6dc43fb68639d37fd09b13512cb1fc41b077d",
    "android-x64": "f3354d22f315fa61c25d4a2691581d6dbba6fe5b71c2dcb338a9a3c7c3e7ce6b",
    "android-arm64": "58932c6c12100990e31be556c9351bc0cf3cf6b6b9e3100a39d6307c2589db8f",
    "macos-x64": "c20c1b995b17cf0353d8c7778f1722df08ae41864b823338094f6809a581fc1b",
    "macos-arm64": "f3a8537441c4b9863ab248b1beb4e897da407d29427d1065484eb62ffa165ce7",
}
ANDROID_NDK = "27.3.13750724"
ANDROID_API = 26
MACOS_MINIMUM = "15.0"
LINUX_DEFINES = ["EGL_NO_X11", "MESA_EGL_NO_X11_HEADERS"]


def fetch(downloads, url, checksum, name=None):
    archive = downloads / (name or url.rsplit("/", 1)[-1])
    if not archive.exists():
        partial = archive.with_suffix(".part")
        subprocess.run(["curl", "-fsSL", "--retry", "3", url, "-o", partial], check=True)
        verify(partial, checksum)
        partial.replace(archive)
    verify(archive, checksum)
    return archive


def verify(path, checksum):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != checksum:
            raise ValueError(f"SHA-256 mismatch for {path}")


def prepare(work, downloads, target, profile):
    source = work / "mediapipe"
    ocv = work / "ocv"
    source.mkdir(parents=True)
    (ocv / "bazel").mkdir(parents=True)
    upstream = fetch(
        downloads, f"https://codeload.github.com/google-ai-edge/mediapipe/tar.gz/{MEDIAPIPE_COMMIT}",
        "09e6bae5999c89de7bf457ee7b36aaa1fd469bcd9d37ed994c6f90212516266e",
    )
    opencv = fetch(
        downloads, f"https://github.com/qigao/ocv/releases/download/v{OCV_VERSION}"
        f"/opencv-4.11.0-static-{profile}.tar.gz", OCV_SHA[profile],
    )
    fetch(downloads, "https://zlib.net/fossils/zlib-1.2.13.tar.gz",
          "b3a24de97a8fdbc835b9833169501030b8977031bcb54b3b3ac13740f846ab30")
    subprocess.run(["tar", "-xzf", upstream, "--strip-components=1", "-C", source], check=True)
    subprocess.run(["tar", "-xzf", opencv, "-C", ocv / "bazel"], check=True)
    (ocv / "WORKSPACE").write_text('workspace(name = "qigao_ocv")\n', encoding="utf-8")
    shutil.copyfile(SDK / "ocv.BUILD", ocv / "bazel/BUILD.bazel")
    workspace = source / "WORKSPACE"
    with workspace.open("a", encoding="utf-8") as stream:
        stream.write(f'\nlocal_repository(name = "qigao_ocv", path = {json.dumps(str(ocv))})\n')
        if target == "android":
            stream.write(
                f'\nandroid_ndk_repository(name = "androidndk", api_level = {ANDROID_API})\n'
                'bind(name = "android/crosstool", actual = "@androidndk//:toolchain")\n'
            )
    for patch in sorted((SDK / "patches").glob("*.diff")):
        subprocess.run(["git", "apply", patch], cwd=source, check=True,
                       env=os.environ | {"GIT_CEILING_DIRECTORIES": str(work)})
    package = source / "qigao_sdk"
    package.mkdir()
    for name in ("BUILD.bazel", "export.bzl"):
        shutil.copyfile(SDK / name, package / name)
    return source, ocv


def copy_paths(execroot, paths, dest):
    for name in paths:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Expected an execroot-relative path, got {name}")
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(execroot / path, target)


def cmake_link_flags(flags, target):
    result = []
    flags = iter(flags)
    for flag in flags:
        if flag in {"-framework", "-weak_framework"}:
            flag += " " + next(flags)
        framework = re.fullmatch(r"(-(?:weak_)?framework) ([A-Za-z0-9_]+)", flag)
        if target == "macos" and framework:
            result.append(f"-Wl,{framework[1]},{framework[2]}")
        elif re.fullmatch(r"(-l[A-Za-z0-9_+:.-]+|-pthread|-Wl,[A-Za-z0-9_+=:,.\-]+)", flag):
            result.append(flag)
        elif target == "macos" and flag in {"-ObjC", "-fobjc-link-runtime"}:
            result.append(flag)
        else:
            raise ValueError(f"Unsupported {target} linker flag: {flag}")
    return list(dict.fromkeys(result))


def write_cmake(manifest, prefix, target, profile):
    lines = [
        'get_filename_component(_mp_root "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)',
        "if(TARGET MediaPipe::Tasks)",
        "  return()",
        "endif()",
        "set(MediaPipe_GPU_ENABLED TRUE)",
        f'set(MediaPipe_SDK_PLATFORM "{profile}")',
        "add_library(MediaPipe::Tasks INTERFACE IMPORTED)",
        "target_compile_features(MediaPipe::Tasks INTERFACE cxx_std_17)",
    ]
    if target == "android":
        lines.append(f'set(MediaPipe_ANDROID_API "{ANDROID_API}")')
    if target == "macos":
        lines.append(f'set(MediaPipe_MACOS_MINIMUM "{MACOS_MINIMUM}")')
    definitions = list(manifest["defines"])
    if target == "linux":
        definitions.extend(LINUX_DEFINES)
    lines.append("target_compile_definitions(MediaPipe::Tasks INTERFACE " +
                 " ".join(json.dumps(value) for value in definitions) + ")")
    for key, system in (("includes", ""), ("system_includes", " SYSTEM")):
        includes = [f'"${{_mp_root}}/include/{path}"' for path in manifest[key]]
        if includes:
            lines.append(f"target_include_directories(MediaPipe::Tasks{system} INTERFACE " +
                         " ".join(includes) + ")")
    for path in manifest["quote_includes"]:
        lines.append(f'target_compile_options(MediaPipe::Tasks INTERFACE '
                     f'"SHELL:-iquote \\"${{_mp_root}}/include/{path}\\"")')
    libraries = []
    for path, alwayslink in manifest["libraries"]:
        archive = f"${{_mp_root}}/lib/archives/{path}"
        libraries.append(f"$<LINK_LIBRARY:WHOLE_ARCHIVE,{archive}>" if alwayslink else archive)
    if target == "macos":
        link = [json.dumps(library) for library in libraries]
    else:
        link = ['"$<LINK_GROUP:RESCAN,' + ",".join(libraries) + '>"']
    link.extend(cmake_link_flags(manifest["link_flags"], target))
    if target == "macos":
        link.append("-lobjc")
    lines.append("target_link_libraries(MediaPipe::Tasks INTERFACE\n  " +
                 "\n  ".join(link) + "\n)")
    lines.append("unset(_mp_root)")
    config = prefix / "lib/cmake/MediaPipe"
    config.mkdir(parents=True)
    (config / "MediaPipeConfig.cmake").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (config / "MediaPipeConfigVersion.cmake").write_text(
        f'set(PACKAGE_VERSION "{MEDIAPIPE_VERSION}")\n'
        'if(PACKAGE_FIND_VERSION VERSION_EQUAL PACKAGE_VERSION)\n'
        '  set(PACKAGE_VERSION_COMPATIBLE TRUE)\n'
        '  set(PACKAGE_VERSION_EXACT TRUE)\n'
        'endif()\n',
        encoding="utf-8",
    )


def stage(execroot, manifest, prefix, source, ocv, target, profile):
    calculator = "inference_calculator_metal" if target == "macos" else "inference_calculator_gl_advanced"
    if not any(alwayslink and Path(path).stem.removesuffix(".pic") == f"lib{calculator}"
               for path, alwayslink in manifest["libraries"]):
        raise ValueError(f"{profile} did not retain the {calculator} GPU calculator")
    include = prefix / "include"
    copy_paths(execroot, manifest["headers"], include)
    for key in ("includes", "quote_includes", "system_includes"):
        for path in manifest[key]:
            if Path(path).is_absolute() or ".." in Path(path).parts:
                raise ValueError(f"Nonrelocatable include directory: {path}")
            (include / path).mkdir(parents=True, exist_ok=True)
    copy_paths(execroot, (path for path, _ in manifest["libraries"]), prefix / "lib/archives")
    write_cmake(manifest, prefix, target, profile)
    metadata = {
        "mediapipe_version": MEDIAPIPE_VERSION,
        "mediapipe_commit": MEDIAPIPE_COMMIT,
        "opencv_sdk_version": OCV_VERSION,
        "platform": profile,
        "gpu": True,
        "gpu_backend": "metal" if target == "macos" else "egl-opengles",
    }
    if target == "android":
        metadata.update(android_api=ANDROID_API, android_ndk=ANDROID_NDK)
    if target == "macos":
        metadata["macos_minimum"] = MACOS_MINIMUM
    (prefix / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    notices = prefix / "licenses"
    notices.mkdir()
    shutil.copyfile(source / "LICENSE", notices / "MediaPipe")
    shutil.copyfile(ocv / "bazel/LICENSE", notices / "OpenCV")
    repositories = {
        Path(path).parts[index + 1]
        for path in manifest["headers"] + [path for path, _ in manifest["libraries"]]
        for index, part in enumerate(Path(path).parts[:-1]) if part == "external"
    }
    for repository in sorted(repositories - {"qigao_ocv"}):
        root = execroot / "external" / repository
        for entry in root.iterdir():
            if entry.is_file() and entry.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")):
                target = notices / repository / entry.name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(entry, target)


def build_flags(target, arch):
    flags = [
        "--repo_env=HERMETIC_PYTHON_VERSION=3.12",
        "--action_env=PYTHONHASHSEED=0",
        "--force_pic",
        "--copt=-fPIC",
        "--cxxopt=-std=c++17",
        "--host_cxxopt=-std=c++17",
    ]
    if target == "linux":
        flags.extend(f"--copt=-D{define}" for define in LINUX_DEFINES)
        if arch == "x64":
            flags.append("--define=xnn_enable_avx512fp16=false")
    elif target == "android":
        cpu, platform_name = {
            "arm64": ("arm64-v8a", "android_arm64_platform"),
            "x64": ("x86_64", "android_x86_64_platform"),
        }[arch]
        flags += [
            "--config=android",
            f"--cpu={cpu}",
            "--incompatible_enable_cc_toolchain_resolution",
            f"--platforms=//mediapipe:{platform_name}",
            "--extra_toolchains=@androidndk//:all",
        ]
    else:
        cpu = {"arm64": "darwin_arm64", "x64": "darwin_x86_64"}[arch]
        flags += [f"--cpu={cpu}", f"--macos_minimum_os={MACOS_MINIMUM}"]
        if arch == "x64":
            flags.append("--define=xnn_enable_avxvnniint8=false")
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["linux", "android", "macos"], default="linux")
    parser.add_argument("--arch", choices=["x64", "arm64"])
    parser.add_argument("--bazel", required=True, type=Path)
    parser.add_argument("--out", default=Path("build-sdk"), type=Path)
    parser.add_argument("--jobs", default=4, type=int)
    args = parser.parse_args()
    host_arch = {"x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine())
    arch = args.arch or host_arch
    host = platform.system()
    if args.target == "android":
        if (host, host_arch) != ("Linux", "x64") or not args.arch:
            parser.error("Android cross-builds require a Linux x64 host and an explicit --arch.")
        if "ANDROID_NDK_HOME" not in os.environ:
            parser.error(f"Set ANDROID_NDK_HOME to Android NDK {ANDROID_NDK}.")
        ndk = Path(os.environ["ANDROID_NDK_HOME"]).resolve()
        properties = (ndk / "source.properties").read_text(encoding="utf-8")
        if f"Pkg.Revision = {ANDROID_NDK}" not in properties.splitlines():
            parser.error(f"Android requires NDK {ANDROID_NDK}.")
        os.environ["ANDROID_NDK_HOME"] = str(ndk)
    elif host != {"linux": "Linux", "macos": "Darwin"}[args.target] or arch != host_arch:
        parser.error("Linux and macOS SDKs must be built on the target OS and architecture.")
    if arch not in {"x64", "arm64"}:
        parser.error("The SDK requires an x64 or ARM64 target.")
    profile = f"{args.target}-{arch}"
    out = args.out.resolve()
    work = out / "source"
    downloads = out / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    if work.exists():
        shutil.rmtree(work)
    source, ocv = prepare(work, downloads, args.target, profile)
    bazel = [args.bazel.resolve(), f"--output_user_root={out / 'bazel'}"]
    flags = build_flags(args.target, arch)
    subprocess.run([
        *bazel, "build", "-c", "opt", f"--jobs={args.jobs}",
        f"--disk_cache={out / 'disk-cache'}", f"--repository_cache={out / 'repository-cache'}",
        f"--distdir={downloads}", *flags, "//qigao_sdk:native",
    ], cwd=source, check=True)
    execroot = Path(subprocess.check_output(
        [*bazel, "info", "execution_root"], cwd=source, text=True,
    ).strip())
    manifest = json.loads((source / "bazel-bin/qigao_sdk/native.json").read_text(encoding="utf-8"))
    prefix = out / "package"
    if prefix.exists():
        shutil.rmtree(prefix)
    stage(execroot, manifest, prefix, source, ocv, args.target, profile)
    archive = out / f"mediapipe-tasks-{MEDIAPIPE_VERSION}-{profile}.tar.gz"
    subprocess.run(["tar", "-czf", archive, "-C", prefix, "."], check=True)
    print(archive)


if __name__ == "__main__":
    main()
