load("@rules_cc//cc:cc_import.bzl", "cc_import")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cc_import(
    name = "egl",
    interface_library = "lib/libEGL_qigao_mp.lib",
    shared_library = "bin/libEGL_qigao_mp.dll",
)
cc_import(
    name = "gles",
    interface_library = "lib/libGLESv2_qigao_mp.lib",
    shared_library = "bin/libGLESv2_qigao_mp.dll",
)
cc_library(
    name = "angle",
    hdrs = glob(["include/**"]),
    includes = ["include"],
    defines = ["EGL_NO_PLATFORM_SPECIFIC_TYPES"],
    deps = [":egl", ":gles"],
    visibility = ["//visibility:public"],
)
