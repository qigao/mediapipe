# MediaPipe Tasks native SDK

The [native SDK workflow](.github/workflows/build-native-sdk.yml) builds the MediaPipe 0.10.26 C++ task and calculator libraries with the released [qigao/ocv](https://github.com/qigao/ocv/releases/tag/v0.1.0) OpenCV SDK. The first SDK profile targets Linux x64 and ARM64 on Ubuntu 24.04 with EGL and OpenGL ES 3.1+. The GPU inference backend requires a compatible device and driver. It includes generated headers, PIC static libraries, and the `MediaPipe::Tasks` CMake target.

Build locally with Bazel 6.5.0, Clang, and the EGL and OpenGL ES development libraries.

```sh
CC=clang CXX=clang++ python3 -B sdk/build.py --bazel /path/to/bazel
```

The SDK archives are staged in `build-sdk/`. Point CMake at the extracted archive and use `find_package(MediaPipe 0.10.26 EXACT CONFIG REQUIRED)`. An `sdk-v*` tag publishes both archives and their SHA-256 checksums after both native SDK builds pass.
