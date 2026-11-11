load("@rules_cc//cc:cc_import.bzl", "cc_import")
load("@rules_cc//cc:cc_library.bzl", "cc_library")

cc_import(
    name = "egl",
    interface_library = "lib/libEGL.dll.a",
    shared_library = "bin/libEGL.dll",
)
cc_import(
    name = "gles",
    interface_library = "lib/libGLESv2.dll.a",
    shared_library = "bin/libGLESv2.dll",
)
cc_library(
    name = "angle",
    hdrs = glob(["include/**"]),
    includes = ["include"],
    deps = [":egl", ":gles"],
    visibility = ["//visibility:public"],
)
