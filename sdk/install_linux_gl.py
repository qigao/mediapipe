"""Stage the pinned GLVND headers and linker libraries on a Linux CI runner."""

import argparse
from pathlib import Path
import subprocess
import tempfile

from build import fetch


GLVND_URL = "https://deb.debian.org/debian/pool/main/libg/libglvnd"
GLVND_VERSION = "1.6.0-1"
PACKAGES = {
    "amd64": {
        "libegl-dev": "0ec9bffb024527dfb61eaeae44966e2b5b3114b3dc315b4117b0df95b1c96ef8",
        "libgles-dev": "901b06c4a5223560617e9362d26ab349f9d9dd3d79e7d87d6ce0b06a7c7128f4",
        "libgl-dev": "ebc12df48ae53924e114d9358ef3da4306d7ef8f7179300af52f1faef8b5db3e",
        "libegl1": "fe4d8b39f6e6fe1a32ab1efd85893553eaa9cf3866aa668ccf355f585b37d523",
        "libgles2": "07b2f51b8aa3c8d6d928133cd46087bd8793d0d67c203f09fc289d45a2cf5f47",
        "libglvnd0": "b6da5b153dd62d8b5e5fbe25242db1fc05c068707c365db49abda8c2427c75f8",
    },
    "arm64": {
        "libegl-dev": "8a3004f892785a5fa4c9f969c116f567a36d1c8e9b3d5fd0403055151e36c7d3",
        "libgles-dev": "941e9963d64479544691f7183fe0eeae32b53b633df71c4c51263517ab2ea8f3",
        "libgl-dev": "56add9e710c072cf56504beed50a639f9f7c64f4e31e66958fa65a566084888c",
        "libegl1": "707097a275155c600e2e9251c4ee7cdfdb2d8f50a678a850a2526a7bc9664166",
        "libgles2": "efeb2717380f8411d66b3f669bb99bbd83ff09db3d4a1661533aa31af659608c",
        "libglvnd0": "d5063205fab5322ee686f33f87c6315b3fcd1335ea4e7bc8202b48ed4f9c9e83",
    },
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arch", choices=["x64", "arm64"])
    args = parser.parse_args()
    deb_arch, multiarch = {"x64": ("amd64", "x86_64-linux-gnu"), "arm64": ("arm64", "aarch64-linux-gnu")}[args.arch]
    downloads = Path("build-sdk/downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        sysroot = Path(directory)
        for package, checksum in PACKAGES[deb_arch].items():
            name = f"{package}_{GLVND_VERSION}_{deb_arch}.deb"
            archive = fetch(downloads, f"{GLVND_URL}/{name}", checksum)
            subprocess.run(["dpkg-deb", "-x", archive, sysroot], check=True)
        includes = sysroot / "usr/include"
        headers = [includes / name for name in ("EGL", "GLES", "GLES2", "GLES3", "KHR")]
        libdir = sysroot / "usr/lib" / multiarch
        libraries = [library for name in ("EGL", "GLESv2", "GLdispatch") for library in libdir.glob(f"lib{name}.so*")]
        subprocess.run(["sudo", "cp", "-a", *headers, "/usr/local/include/"], check=True)
        subprocess.run(["sudo", "cp", "-a", *libraries, "/usr/local/lib/"], check=True)
        subprocess.run(["sudo", "ldconfig"], check=True)


if __name__ == "__main__":
    main()
