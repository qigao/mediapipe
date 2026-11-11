# MediaPipe Tasks native SDK

The [native SDK workflow](.github/workflows/build-native-sdk.yml) builds the MediaPipe 1.2.2 C++ task and calculator libraries with the released [qigao/ocv](https://github.com/qigao/ocv/releases/tag/v0.1.0) OpenCV SDK. Each archive includes generated headers, static libraries, and the `MediaPipe::Tasks` CMake target. GPU inference requires a compatible device and driver.

| Target | Architectures | Inference backend | Build host |
| --- | --- | --- | --- |
| Linux | x64, ARM64 | EGL and OpenGL ES 3.1+ | Ubuntu 24.04 on the target architecture |
| Android | x86_64, arm64-v8a | EGL and OpenGL ES 3.1+ | Linux x64 with NDK r27d, API 26 |
| macOS | ARM64 | Metal | macOS 15 on ARM64 |
| Windows | x64, ARM64 | CPU with XNNPACK | Windows on the target architecture, LLVM-MinGW |

Build with Bazel 7.7.0 and Clang (C++20). Install the EGL and OpenGL ES development headers on Linux. Set `ANDROID_NDK_HOME` to NDK 27.3.13750724 for Android cross-builds.

```sh
CC=clang CXX=clang++ python3 -B sdk/build.py --target linux --arch x64 --bazel /path/to/bazel
```

On Windows, select `BaseOptions::CPU` to use XNNPACK. The CMake package exposes `MediaPipe_CPU_DELEGATE=xnnpack` and `MediaPipe_GPU_ENABLED=FALSE`. XNNPACK's pthreadpool links the C11 thread implementation from SaltsBase 0.1.3 statically.

The SDK archives are staged in `build-sdk/`. Point CMake at the archive for the target OS and architecture and use `find_package(MediaPipe 1.2.2 EXACT CONFIG REQUIRED)`. An `sdk-v*` tag publishes the seven SDK archives and their SHA-256 checksums after the build jobs pass.
