# MediaPipe × opencv_lite CI Build

> Pre-built packages of [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) using [zihaomu/opencv_lite](https://github.com/zihaomu/opencv_lite) as the OpenCV backend — a lightweight, edge-optimized alternative with pluggable AI inference (ONNX Runtime, MNN, TFLite).

---

## Badges

| Platform | Status |
|----------|--------|
| 🐧 Linux x86_64 | [![Build MediaPipe + opencv_lite — Linux](../../actions/workflows/build-mediapipe-opencv-lite.yml/badge.svg)](../../actions/workflows/build-mediapipe-opencv-lite.yml) |
| 🪟 Windows x64 | [![Build MediaPipe + opencv_lite — Windows](../../actions/workflows/build-mediapipe-opencv-lite-windows.yml/badge.svg)](../../actions/workflows/build-mediapipe-opencv-lite-windows.yml) |
| 🤖 Android | [![Build MediaPipe + opencv_lite — Android](../../actions/workflows/build-mediapipe-opencv-lite-android.yml/badge.svg)](../../actions/workflows/build-mediapipe-opencv-lite-android.yml) |
| 🍎 iOS | [![Build MediaPipe + opencv_lite — iOS](../../actions/workflows/build-mediapipe-opencv-lite-ios.yml/badge.svg)](../../actions/workflows/build-mediapipe-opencv-lite-ios.yml) |

---

## Why opencv_lite?

Standard OpenCV brings **100+ MB** of modules you probably don't need. `opencv_lite` trims it down to the essentials:

| Feature | Standard OpenCV | opencv_lite |
|---------|----------------|-------------|
| Modules | 50+ | core, imgproc, dnn, video, highgui |
| Binary size | ~100 MB | ~10 MB |
| DNN backends | OpenCV DNN only | **ONNX Runtime, MNN, TFLite** |
| ONNX operator coverage | ~30% | **~92%** |
| Build system | CMake / Bazel | CMake only (simpler) |
| Drop-in API | ✅ | ✅ |

---

## Artifacts

Every successful CI run uploads versioned packages to **GitHub Actions Artifacts** (retained 30 days).  
Pushes to a version tag (e.g. `v1.0.0`) additionally publish to **GitHub Releases**.

### Download a pre-built package

1. Go to [Actions](../../actions) and select the latest successful workflow run for your platform.
2. Scroll to **Artifacts** at the bottom of the run summary.
3. Download and extract the package for your platform.

| Platform | Artifact name | Format |
|----------|--------------|--------|
| Linux x86_64 | `mediapipe-opencv_lite-linux-x86_64-<date>-<sha>` | `.tar.gz` |
| Windows x64 | `mediapipe-opencv_lite-windows-x64-<date>-<sha>` | `.zip` |
| Android arm64-v8a | `mediapipe-android-arm64-v8a` | `.aar` |
| Android armeabi-v7a | `mediapipe-android-armeabi-v7a` | `.aar` |
| Android x86_64 | `mediapipe-android-x86_64` | `.aar` |
| iOS | `mediapipe-ios-framework` | `.zip` (XCFramework) |

---

## Package Contents

### Linux `.tar.gz`

```
mediapipe-opencv_lite-linux-x86_64-<ver>/
├── bin/
│   └── hello_world              # MediaPipe example binary
├── lib/
│   ├── libopencv_core.so*       # opencv_lite shared libs
│   ├── libopencv_imgproc.so*
│   ├── libopencv_dnn.so*
│   ├── libopencv_video.so*
│   ├── libopencv_highgui.so*
│   └── libonnxruntime.so*       # ONNX Runtime (opencv_lite dependency)
├── include/
│   └── opencv2/                 # C++ headers (drop-in for standard OpenCV)
└── README.txt
```

**Quick start:**
```bash
tar -xzf mediapipe-opencv_lite-linux-x86_64-*.tar.gz
cd mediapipe-opencv_lite-linux-x86_64-*/
export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH
./bin/hello_world
```

---

### Windows `.zip`

```
mediapipe-opencv_lite-windows-x64-<ver>/
├── bin/
│   ├── hello_world.exe          # MediaPipe example binary
│   ├── opencv_core.dll          # opencv_lite DLLs
│   ├── opencv_imgproc.dll
│   ├── opencv_dnn.dll
│   └── onnxruntime.dll          # ONNX Runtime DLL
├── lib/
│   └── opencv_*.lib             # Import libraries (for linking)
├── include/
│   └── opencv2/                 # C++ headers
└── README.txt
```

**Quick start:**
```powershell
Expand-Archive mediapipe-opencv_lite-windows-x64-*.zip -DestinationPath .
cd mediapipe-opencv_lite-windows-x64-*\
$env:PATH = "$PWD\bin;$env:PATH"
.\bin\hello_world.exe
```

---

### Android `.aar`

Each ABI (arm64-v8a, armeabi-v7a, x86_64) is a separate `.aar` artifact.

**Gradle integration:**
```groovy
// settings.gradle — add your local AAR
dependencies {
    implementation fileTree(dir: 'libs', include: ['*.aar'])
    // or from a local Maven repo if published
}
```

**Supported ABIs:**

| ABI | Target devices |
|-----|---------------|
| `arm64-v8a` | Modern Android phones (2016+) |
| `armeabi-v7a` | Older 32-bit ARM devices |
| `x86_64` | Android emulators / x86 tablets |

---

### iOS XCFramework `.zip`

Contains a fat framework with slices for:
- `arm64` — physical iPhone/iPad devices
- `arm64` + `x86_64` — simulators (fat binary via `lipo`)

**Xcode integration:**
1. Unzip `mediapipe-ios-framework.zip`.
2. Drag `MediaPipeFramework.xcframework` into your Xcode project.
3. In **General → Frameworks, Libraries, and Embedded Content**, set it to **Embed & Sign**.

---

## Building Locally

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [Bazelisk](https://github.com/bazelbuild/bazelisk) | latest | Manages Bazel version automatically |
| [CMake](https://cmake.org) | ≥ 3.20 | For building opencv_lite |
| [ONNXRuntime](https://github.com/microsoft/onnxruntime/releases) | v1.14–v1.22 | Required by opencv_lite |
| Python | ≥ 3.9 | Required by MediaPipe |
| GCC / Clang / MSVC | — | Platform C++ compiler |

### Step 1 — Build opencv_lite

```bash
# Download ONNXRuntime
wget https://github.com/microsoft/onnxruntime/releases/download/v1.18.1/onnxruntime-linux-x64-1.18.1.tgz
mkdir -p /opt/onnxruntime
tar -xzf onnxruntime-linux-x64-1.18.1.tgz -C /opt/onnxruntime --strip-components=1
export ORT_SDK=/opt/onnxruntime

# Build opencv_lite
git clone https://github.com/zihaomu/opencv_lite.git
mkdir -p opencv_lite/build && cd opencv_lite/build
cmake .. -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DORT_SDK=$ORT_SDK \
  -DBUILD_SHARED_LIBS=ON
ninja -j$(nproc)
sudo ninja install && sudo ldconfig
```

### Step 2 — Configure MediaPipe

```bash
git clone https://github.com/google-ai-edge/mediapipe.git
cd mediapipe

# Point MediaPipe to your opencv_lite install (/usr/local)
# Edit WORKSPACE — update linux_opencv path:
#   path = "/usr/local"
# Edit third_party/opencv_linux.BUILD — update linkopts to match
# the .so files actually built by opencv_lite (core, imgproc, dnn, video, highgui)
```

> **Tip:** The CI workflows automate these edits using Python scripts — see [`.github/workflows/`](.github/workflows/) for the exact patching logic.

### Step 3 — Build MediaPipe

```bash
bazel build \
  -c opt \
  --define MEDIAPIPE_DISABLE_GPU=1 \
  //mediapipe/examples/desktop/hello_world:hello_world

GLOG_logtostderr=1 bazel-bin/mediapipe/examples/desktop/hello_world/hello_world
```

---

## Workflows Overview

```
.github/workflows/
├── build-mediapipe-opencv-lite.yml          # Linux x86_64
├── build-mediapipe-opencv-lite-windows.yml  # Windows x64 (MSVC)
├── build-mediapipe-opencv-lite-android.yml  # Android (arm64-v8a, armeabi-v7a, x86_64)
└── build-mediapipe-opencv-lite-ios.yml      # iOS (arm64 device + simulator fat binary)
```

| Step | Linux | Windows | Android | iOS |
|------|-------|---------|---------|-----|
| Runner | ubuntu-22.04 | windows-2022 | ubuntu-22.04 | macos-13 |
| Compiler | GCC | MSVC (VS 2022) | NDK Clang | Xcode Clang |
| opencv_lite build | CMake native | CMake + MSVC | CMake + NDK cross-compile | CMake + Xcode toolchain |
| MediaPipe build | `bazel build` | `bazel build` | `bazel build --config=android_arm64` | `bazel build --config=ios_arm64` |
| Package format | `.tar.gz` | `.zip` | `.aar` | XCFramework `.zip` |
| GitHub Release | ✅ on `v*` tag | ✅ on `v*` tag | ✅ on `v*` tag | ✅ on `v*` tag |

---

## Releasing a New Version

```bash
git tag v1.0.0
git push origin v1.0.0
```

All four workflows trigger automatically, build their packages, and attach them to a new **GitHub Release** named `v1.0.0`.

---

## Dependency Versions

| Dependency | Version | Why |
|------------|---------|-----|
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) | `master` | Official Google AI Edge framework |
| [opencv_lite](https://github.com/zihaomu/opencv_lite) | `main` | Lightweight OpenCV backend |
| [ONNXRuntime](https://github.com/microsoft/onnxruntime) | `1.18.1` | AI inference backend for opencv_lite |
| [Bazelisk](https://github.com/bazelbuild/bazelisk) | latest | Manages Bazel version from `.bazelversion` |
| Android NDK | `r25c` | Tested NDK for Android cross-compilation |
| iOS deployment target | `15.0` | Minimum iOS version |

---

## Troubleshooting

### `linux_opencv path not found in WORKSPACE`
MediaPipe's WORKSPACE format may have changed. Open `mediapipe/WORKSPACE`, search for `linux_opencv`, and manually update the `path` to `/usr/local`.

### Missing OpenCV module errors (e.g. `calib3d`, `features2d`)
opencv_lite intentionally omits modules like `calib3d`, `features2d`, and `imgcodecs`. The CI workflow auto-generates `opencv_linux.BUILD` with only the modules that were actually built. If a MediaPipe calculator requires a missing module, you may need to either:
- Exclude that calculator from the build target, or
- Use a full OpenCV build instead of opencv_lite for that specific calculator.

### Android NDK version mismatch
MediaPipe's `WORKSPACE` pins a specific NDK version via `android_ndk_repository`. If the workflow NDK version doesn't match, update `NDK_VERSION` in the workflow env or change the pin in `WORKSPACE`.

### iOS simulator build fails on Apple Silicon
The simulator fat binary lipo step merges `arm64` + `x86_64` slices. On Apple Silicon Mac runners, the `x86_64` simulator slice may require Rosetta. The `macos-13` runner (Intel) avoids this issue.

---

## License

- **MediaPipe**: [Apache 2.0](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)
- **opencv_lite**: [Apache 2.0](https://github.com/zihaomu/opencv_lite/blob/main/LICENSE)
- **ONNXRuntime**: [MIT](https://github.com/microsoft/onnxruntime/blob/main/LICENSE)
- **This repository** (CI scripts): [MIT](LICENSE)
