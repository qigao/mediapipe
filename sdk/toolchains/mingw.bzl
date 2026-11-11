"""GNU-driver LLVM-MinGW toolchain; target libraries use the OCV SDK's ABI."""

load("@bazel_tools//tools/build_defs/cc:action_names.bzl", "ACTION_NAMES")
load("@bazel_tools//tools/cpp:cc_toolchain_config_lib.bzl", "artifact_name_pattern", "feature", "flag_group", "flag_set", "tool_path")
load(":compiler.bzl", "COMPILER_ROOT")

def _config_impl(ctx):
    triple = {"x64": "x86_64-w64-mingw32", "arm64": "aarch64-w64-mingw32"}[ctx.attr.arch]
    compile_actions = [
        ACTION_NAMES.c_compile,
        ACTION_NAMES.cpp_compile,
        ACTION_NAMES.assemble,
        ACTION_NAMES.preprocess_assemble,
        ACTION_NAMES.cpp_header_parsing,
    ]
    link_actions = [
        ACTION_NAMES.cpp_link_executable,
        ACTION_NAMES.cpp_link_dynamic_library,
        ACTION_NAMES.cpp_link_nodeps_dynamic_library,
    ]
    return cc_common.create_cc_toolchain_config_info(
        ctx = ctx,
        toolchain_identifier = "llvm-mingw-" + ctx.attr.arch,
        host_system_name = "local",
        target_system_name = triple,
        target_cpu = {"x64": "x64_windows", "arm64": "arm64_windows"}[ctx.attr.arch],
        target_libc = "ucrt",
        compiler = "mingw-gcc",
        abi_version = "local",
        abi_libc_version = "local",
        cxx_builtin_include_directories = [COMPILER_ROOT],
        artifact_name_patterns = [
            artifact_name_pattern(category_name = "executable", prefix = "", extension = ".exe"),
            artifact_name_pattern(category_name = "dynamic_library", prefix = "lib", extension = ".dll"),
        ],
        tool_paths = [
            tool_path(name = "gcc", path = COMPILER_ROOT + "/bin/" + triple + "-clang++.exe"),
            tool_path(name = "ar", path = COMPILER_ROOT + "/bin/llvm-ar.exe"),
            tool_path(name = "ld", path = COMPILER_ROOT + "/bin/ld.lld.exe"),
            tool_path(name = "nm", path = COMPILER_ROOT + "/bin/llvm-nm.exe"),
            tool_path(name = "objcopy", path = COMPILER_ROOT + "/bin/llvm-objcopy.exe"),
            tool_path(name = "objdump", path = COMPILER_ROOT + "/bin/llvm-objdump.exe"),
            tool_path(name = "strip", path = COMPILER_ROOT + "/bin/llvm-strip.exe"),
            tool_path(name = "cpp", path = COMPILER_ROOT + "/bin/" + triple + "-clang++.exe"),
            tool_path(name = "gcov", path = COMPILER_ROOT + "/bin/llvm-cov.exe"),
        ],
        features = [
            feature(name = "targets_windows", enabled = True),
            feature(name = "supports_dynamic_linker", enabled = True),
            feature(name = "c_language", enabled = True, flag_sets = [flag_set(
                actions = [ACTION_NAMES.c_compile],
                flag_groups = [flag_group(flags = ["-x", "c", "-std=c11"])],
            )]),
            feature(name = "compiler_flags", enabled = True, flag_sets = [flag_set(
                actions = compile_actions,
                flag_groups = [flag_group(flags = ["-D_WIN32_WINNT=0x0A00", "-DNOMINMAX"])],
            )]),
            feature(name = "default_link_flags", enabled = True, flag_sets = [flag_set(
                actions = link_actions,
                flag_groups = [flag_group(flags = ["-static-libstdc++", "-static-libgcc"])],
            )]),
        ],
    )

mingw_config = rule(
    implementation = _config_impl,
    attrs = {"arch": attr.string(mandatory = True, values = ["x64", "arm64"])},
    provides = [CcToolchainConfigInfo],
)
