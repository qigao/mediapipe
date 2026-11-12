cc_import(
    name = "imgproc",
    static_library = select({
        "@platforms//os:windows": "lib/libopencv_imgproc4110.a",
        "//conditions:default": "lib/libopencv_imgproc.a",
    }),
)

cc_import(
    name = "core",
    static_library = select({
        "@platforms//os:windows": "lib/libopencv_core4110.a",
        "//conditions:default": "lib/libopencv_core.a",
    }),
)

cc_library(
    name = "opencv",
    hdrs = glob([
        "include/opencv2/**",
        "include/opencv4/opencv2/**",
        "sdk/native/jni/include/opencv2/**",
    ]),
    includes = select({
        "@platforms//os:android": ["sdk/native/jni/include"],
        "@platforms//os:windows": ["include"],
        "//conditions:default": ["include/opencv4"],
    }),
    linkopts = select({
        "@platforms//os:windows": ["-luser32", "-ladvapi32", "-lole32"],
        "@platforms//os:android": ["-landroid", "-ldl", "-llog", "-lm"],
        "@platforms//os:macos": ["-framework Accelerate", "-framework Foundation"],
        "@platforms//os:linux": ["-ldl", "-lm", "-lpthread", "-lrt"],
    }),
    deps = [":imgproc", ":core", "@zlib//:zlib"] + select({
        "@platforms//os:android": ["@androidndk//:cpufeatures"],
        "//conditions:default": [],
    }),
    visibility = ["//visibility:public"],
)
