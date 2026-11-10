cc_import(
    name = "imgproc",
    static_library = "lib/libopencv_imgproc.a",
)

cc_import(
    name = "core",
    static_library = "lib/libopencv_core.a",
)

cc_library(
    name = "opencv",
    hdrs = glob(["include/opencv4/opencv2/**"]),
    includes = ["include/opencv4"],
    linkopts = ["-ldl", "-lm", "-lpthread", "-lrt"],
    deps = [":imgproc", ":core", "@zlib//:zlib"],
    visibility = ["//visibility:public"],
)
