# MediaPipe Tasks native SDK

The [native SDK workflow](.github/workflows/build-native-sdk.yml) builds the MediaPipe 1.2.2 C++ task and calculator libraries with the released [qigao/ocv](https://github.com/qigao/ocv/releases/tag/v0.1.0) OpenCV SDK. Each archive includes generated headers, static libraries, and the `MediaPipe::Tasks` CMake target. GPU inference requires a compatible device and driver.

| Target | Architectures | GPU backend | Build host |
| --- | --- | --- | --- |
| Linux | x64, ARM64 | EGL and OpenGL ES 3.1+ | Ubuntu 24.04 on the target architecture |
| Android | x86_64, arm64-v8a | EGL and OpenGL ES 3.1+ | Linux x64 with NDK r27d, API 26 |
| macOS | x64, ARM64 | Metal | macOS 15 on the target architecture |
| Windows | x64, ARM64 | ANGLE / Vulkan, OpenGL ES 3.1+ | Windows on the target architecture, LLVM-MinGW |

Build with Bazel 7.7.0 and Clang (C++20). Install the EGL and OpenGL ES development headers on Linux. Set `ANDROID_NDK_HOME` to NDK 27.3.13750724 for Android cross-builds.

```sh
CC=clang CXX=clang++ python3 -B sdk/build.py --target linux --arch x64 --bazel /path/to/bazel
```

Windows replaces the GL context's pthread calls with the unchanged C11 thread implementation from pinned SaltsBase 0.1.3 sources, compiled as a private static dependency. Its thread handles and TSS keys remain inside MediaPipe; there is no second Core DLL. ANGLE's official GN build produces Vulkan-only C API DLLs with clang-cl; GNU import libraries connect them to LLVM-MinGW-built MediaPipe/GDMP. SDK consumers must deploy `bin/libEGL.dll` and `bin/libGLESv2.dll` beside the application executable.

The Windows runtime explicitly selects ANGLE/Vulkan, requires GLES 3.1, and rejects CPU/software Vulkan devices. It uses device capabilities rather than an NVIDIA/Intel/AMD allowlist. No CUDA SDK is required. Explicit GPU requests never select CPU inference calculators. Building an archive is separate from physical-device qualification; Windows GPU inference and device selection remain tracked in [#2](https://github.com/qigao/mediapipe/issues/2).

The SDK archives are staged in `build-sdk/`. Point CMake at the archive for the target OS and architecture and use `find_package(MediaPipe 1.2.2 EXACT CONFIG REQUIRED)`. An `sdk-v*` tag publishes the SDK archives and their SHA-256 checksums after all eight build jobs pass.
