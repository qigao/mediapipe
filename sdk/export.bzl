"""Export the actual C++ link and header closure selected by Bazel."""

def _export_cc_sdk_impl(ctx):
    info = cc_common.merge_cc_infos(cc_infos = [dep[CcInfo] for dep in ctx.attr.deps])
    compilation = info.compilation_context
    inputs = info.linking_context.linker_inputs.to_list()
    libraries = {}
    flags = []
    for linker_input in inputs:
        for extra in linker_input.additional_inputs:
            # Bazel uses this file to assemble the Objective-C archive with libtool.
            if extra.basename != linker_input.owner.name + "-archive.objlist":
                fail("Unsupported additional linker input {} in {}".format(extra.path, linker_input.owner))
        flags.extend(linker_input.user_link_flags)
        for lib in linker_input.libraries:
            archive = lib.pic_static_library or lib.static_library
            if not archive:
                fail("The SDK requires a static archive for {}".format(linker_input.owner))
            libraries[archive] = libraries.get(archive, False) or lib.alwayslink

    manifest = ctx.actions.declare_file(ctx.label.name + ".json")
    ctx.actions.write(manifest, json.encode({
        "defines": compilation.defines.to_list(),
        "headers": [header.path for header in compilation.headers.to_list()],
        "includes": compilation.includes.to_list(),
        "quote_includes": compilation.quote_includes.to_list(),
        "system_includes": compilation.system_includes.to_list(),
        "libraries": [[archive.path, alwayslink] for archive, alwayslink in libraries.items()],
        "link_flags": flags,
    }))
    return [DefaultInfo(files = depset([manifest] + libraries.keys(), transitive = [compilation.headers]))]

export_cc_sdk = rule(
    implementation = _export_cc_sdk_impl,
    attrs = {"deps": attr.label_list(providers = [CcInfo], mandatory = True)},
)
