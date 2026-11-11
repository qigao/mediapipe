load("@rules_cc//cc:cc_library.bzl", "cc_library")

# Compile the released Salts implementation unchanged as a private static
# dependency of MediaPipe's GL context and pthreadpool.
cc_library(
    name = "threads",
    srcs = [
        "core/src/atomic/portable_atomic.c",
        "core/src/threads/c11_sleep_win.c",
        "core/src/threads/c11_threads.c",
        "core/src/threads/c11_tss.c",
        "core/src/threads/portable_once.c",
        "core/src/threads/portable_thread_win.c",
        "core/src/threads/portable_tss_win.c",
    ],
    hdrs = glob(["core/include/**/*.h", "core/src/threads/*.h"]),
    includes = ["core/include", "core/include/threads"],
    local_defines = ["SALTS_API=", "WIN32_LEAN_AND_MEAN", "_WIN32_WINNT=0x0A00"],
    visibility = ["//visibility:public"],
)
