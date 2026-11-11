# MediaPipe Tasks native SDK

The [native SDK workflow](.github/workflows/build-native-sdk.yml) builds the MediaPipe 1.2.2 C++ task and calculator libraries with the released [qigao/ocv](https://github.com/qigao/ocv/releases/tag/v0.1.0) OpenCV SDK. Each archive includes generated headers, static libraries, and the `MediaPipe::Tasks` CMake target. GPU inference requires a compatible device and driver.

| Target | Architectures | Inference backend | Build host |
| --- | --- | --- | --- |
| Linux | x64, ARM64 | EGL and OpenGL ES 3.1+ | Ubuntu 24.04 on the target architecture |
| Android | x86_64, arm64-v8a | EGL and OpenGL ES 3.1+ | Linux x64 with NDK r27d, API 26 |
| macOS | ARM64 | Metal | macOS 15 on ARM64 |
| Windows | x64, ARM64 | CPU with XNNPACK | Windows on the target architecture, LLVM-MinGW |

Build with Bazel 7.7.0 and a C++20 compiler. Install the EGL and OpenGL ES development headers on Linux. Set `ANDROID_NDK_HOME` to NDK 27.3.13750724 for Android cross-builds.

```sh
CC=clang CXX=clang++ python3 -B sdk/build.py --target linux --arch x64 --bazel /path/to/bazel
```

On Windows, select `BaseOptions::CPU` to use XNNPACK. The CMake package exposes `MediaPipe_CPU_DELEGATE=xnnpack` and `MediaPipe_GPU_ENABLED=FALSE`. XNNPACK's pthreadpool links the C11 thread implementation from SaltsBase 0.1.3 statically.

The [MSVC workflow](.github/workflows/build-msvc-sdk.yml) builds Windows x64 and ARM64 SDKs against matching OpenCVLite MSVC artifacts. It uploads `windows-x64-msvc` and `windows-arm64-msvc` archives for the MSVC C++ ABI with the DLL runtime (`/MD`). For a local MSVC build, pass `--windows-toolchain msvc --opencv-archive /path/to/opencv-sdk.tar.gz` and use Visual Studio Build Tools. Set `--bazel-root C:/b` to keep generated header paths short.

The SDK workflows also build the upstream Tasks C shared library for each target. The shared library includes vision, audio, text, decision, and metadata APIs and links OpenCVLite statically. CI uploads `libmediapipe.dll`, `libmediapipe.so`, or `libmediapipe.dylib` as a separate artifact and validates the image API on desktop and the ELF ABI on Android. Pass `--shared` to build the shared library locally. Linux systems need the EGL and OpenGL ES runtime libraries to load it.

The SDK archives are staged in `build-sdk/`. Point CMake at the archive for the target OS and architecture and use `find_package(MediaPipe 1.2.2 EXACT CONFIG REQUIRED)`. An `sdk-v*` tag publishes the seven SDK archives and their SHA-256 checksums after the build jobs pass.
