"""Validate the Tasks C shared library built for the selected target."""

import argparse
import ctypes as c
from pathlib import Path
import re
import subprocess


def check_runtime(library):
    dll = c.CDLL(str(library.resolve()))
    create = dll.MpImageCreateFromUint8Data
    create.argtypes = [c.c_int, c.c_int, c.c_int, c.POINTER(c.c_uint8),
                       c.c_int, c.POINTER(c.c_void_p), c.POINTER(c.c_char_p)]
    create.restype = c.c_int
    width = dll.MpImageGetWidth
    width.argtypes = [c.c_void_p]
    width.restype = c.c_int
    free = dll.MpImageFree
    free.argtypes = [c.c_void_p]
    free.restype = None

    image = c.c_void_p()
    error = c.c_char_p()
    rgb = (c.c_uint8 * 6)(0, 128, 255, 255, 128, 0)
    status = create(1, 2, 1, rgb, len(rgb), c.byref(image), c.byref(error))
    if status:
        raise SystemExit(f"MpImageCreateFromUint8Data returned {status}: {error.value!r}")
    try:
        if width(image) != 2:
            raise SystemExit("Tasks C library returned an unexpected image width")
    finally:
        free(image)
    print("Tasks C library loaded and processed an RGB image")


def check_android(library, arch, readelf):
    output = subprocess.check_output(
        [readelf, "--file-header", "--program-headers", "--dynamic", "--dyn-syms", "--wide", library],
        text=True,
    )
    machine = {"x64": "Advanced Micro Devices X86-64", "arm64": "AArch64"}[arch]
    if not re.search(rf"Machine:\s+{re.escape(machine)}$", output, re.MULTILINE):
        raise SystemExit(f"{library.name} has the wrong Android architecture for {arch}")
    if not re.search(r"\(SONAME\).*\[libmediapipe\.so\]", output):
        raise SystemExit(f"{library.name} has the wrong Android SONAME")
    alignments = re.findall(r"^\s*LOAD .+ (0x[0-9a-fA-F]+)$", output, re.MULTILINE)
    if not alignments or min(int(alignment, 16) for alignment in alignments) < 16384:
        raise SystemExit(f"{library.name} requires 16 KiB ELF load alignment")
    if not re.search(r"\bGLOBAL\s+DEFAULT\s+\d+\s+MpImageCreateFromUint8Data$", output, re.MULTILINE):
        raise SystemExit(f"{library.name} is missing the Tasks C image API")
    print(f"Android {arch} Tasks C library verified with 16 KiB load alignment")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path)
    parser.add_argument("--android", nargs=2, metavar=("ARCH", "READELF"))
    args = parser.parse_args()
    if args.android:
        check_android(args.library, *args.android)
    else:
        check_runtime(args.library)


if __name__ == "__main__":
    main()
