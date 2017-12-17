load("@io_bazel_rules_rust//rust:rust.bzl",
    "rust_binary",
    "rust_library"
)

#rust_binary(
#    name = "cargo",
#    srcs = glob(["cargo_srcs/cargo-*/src/**/*.rs",]),
#    deps = [],
#)

#rust_library(
#    name = "hello_lib",
#    srcs = [
#        "src/greeter.rs",
#        "src/lib.rs",
#    ],
#)

def _local_cargo_repository_impl(ctx):
    print("!!!!")
    repo_path = ctx.path(ctx.attr.path)
    print(repo_path)
    print(ctx.path("."))

    ctx.execute([ctx.path(ctx.attr._local_cargo_repository_tool), "crate/BUILD"])

    #ctx.file("crate/BUILD", """filegroup(name="crate")""")

local_cargo_repository = repository_rule(
    local = True,
    attrs = {
        "path": attr.string(
            mandatory = True,
        ),
        "_local_cargo_repository_tool": attr.label(
            default = Label("@fake//:local_cargo_repository_tool"),
            cfg = "host",
            executable = True,
            allow_files = True,
            single_file = True,
        ),
    },
    implementation = _local_cargo_repository_impl,
)

def _index_repository(ctx, root, repository):
    if not repository.endswith(".git"):
        repository += ".git"

    # TODO: Use git_repository if possible instead
    result = ctx.execute(["git", "clone", repository, root])
    if result.return_code != 0:
        fail("Unable to clone index repository", repository)

def _get_features(crate_name, crate_version, crates):
    for crate in crates:
        if not crate_name in crate.deps:
            continue

        info = crate.deps[crate_name]
        if info['version'] == crate_version:
            return info['features']

def _cargo_repository_impl(ctx):
    print("starting cargo repository")

    java = ctx.path(ctx.attr._java_bin)
    python = ctx.which("python")

    index_repository_root = "{name}_index_repo".format(name=ctx.attr.name)
    repository = ctx.attr.repository

    _index_repository(ctx, index_repository_root, repository)

    # Convert crate to crate path (? Probably in script)

    cargo_dependency_resolver = str(ctx.path(ctx.attr._cargo_dependency_resolver))
    java_cargo_dependency_resolver = str(ctx.path(ctx.attr._java_cargo_dependency_resolver))


    # cargo_dependency resolver for crates -> crate_namve-1.2.3  ["dep_1-0.0.1", "dep_2-1.2.3"] dep_1-0.0.1 []
    #
    # result = ctx.execute([python, cargo_dependency_resolver, ctx.attr.crate, ctx.attr.version, index_repository_root], quiet=False)
    result = ctx.execute([java, "-jar", java_cargo_dependency_resolver, ctx.attr.crate, ctx.attr.version, index_repository_root], quiet=False)
    if result.return_code != 0:
        fail("Unable to resolve cargo dependencies", result.stderr)

    crates = []
    for line in result.stdout.split('\n'):
        # Ignore empty lines (like the final one)
        if len(line) == 0:
            continue

        entries = line.split(' ')

        crate_name = entries[0]
        crate_version = entries[1]

        deps = {}
        dep_name = None
        i = 0
        for entry in entries[2:]:
            if i % 3 == 0:
                # Carate name
                dep_name = entry
            elif i % 3 == 1:
                # Crate version
                deps[dep_name] = { "version": entry }
            else:
                # Features
                deps[dep_name]["features"] = entry.split(":")
            i += 1

        crates.append(struct(
            name = crate_name,
            version = crate_version,
            deps = deps,
        ))

    print(crates)

    hashes = ctx.attr.sha256hashes
    for crate in crates:
        targz_loc = "{name}-{version}.crate".format(name=crate.name, version=crate.version)
        ctx.download(
            url = "https://crates.io/api/v1/crates/{name}/{version}/download".format(name=crate.name, version=crate.version),
            output = targz_loc,
            #type = "tar.gz",
            sha256 = hashes.get(crate.name + "-" + crate.version, ''),
        )
        ret = ctx.execute(["tar", "-xzf", str(ctx.path(targz_loc))], quiet=True)
        if ret.return_code != 0:
            fail("TarGZ extracting failed for " + targz_loc, str(ret.return_code)) ##### ! the index its own repository_rule as well as each of the downloads to prevent redownloads!!!!!

        # This is the root folder of all crates so this is assumed "by convention"
        expanded_loc = "{name}-{version}".format(name=crate.name, version=crate.version)

        # print(expanded_loc + " --- " + crate.name)

        crate_root_finder = str(ctx.path(ctx.attr._crate_root_finder))
        ret = ctx.execute([python, crate_root_finder, expanded_loc, crate.name], quiet=False)

        if ret.return_code != 0:
            continue # TODO remove
            fail("Could not find the root of crate " + crate.name, str(ret.return_code))

        print("crate_root_finder: " + ret.stdout)

        crate_root = None
        crate_features = []
        for line in ret.stdout.split("\n"):
            line = line.strip()
            path_prefix = 'path '
            features_prefix = 'features '
            if line.startswith(path_prefix):
                crate_root = line[len(path_prefix):].strip()
            if line.startswith(features_prefix):
                crate_features = line[len(features_prefix):].strip().split(' ')

        # TODO: Remove this check as it shouldn't be necesary
        if _get_features(crate.name, crate.version, crates) != None:
            crate_features.extend(_get_features(crate.name, crate.version, crates))

        print("Crate: " + str(crate.name))
        print("CR: " + str(crate_root))
        print("CF: " + str(crate_features))

        ctx.file(expanded_loc + "/BUILD", """
load("@io_bazel_rules_rust//rust:rust.bzl", "rust_library")

rust_library(
    name = "{name}",
    srcs = glob([
        "*.rs",
        "**/*.rs",
        # "src/*.rs",
        # "src/**/*.rs",
    ]),
    deps = {deps},
    crate_root = {crate_root},
    crate_features = {crate_features},
    visibility = [ "//visibility:public" ],
)
            """.format(
                name=crate.name.replace('-', '_'),
                deps=repr(["//" + name + "-" + info['version'] + ":" + name.replace('-', '_')
                        for name, info in crate.deps.items()]),
                crate_root=repr(crate_root) if crate_root else None,
                crate_features=repr(crate_features) if crate_features else None,
            )
        )
    # Loop over crates and deps and generate BUILD files

    # Generate exposed BUILD file for top level crate


    # fake build file so it can take place
    ctx.file("BUILD", "filegroup(name='cargo',srcs=[])", executable=False)

def _cargo_repo_index_impl(ctx):
    repository = ctx.attr.repository
    if not repository.endswith(".git"):
        repository += ".git"

    print("Repository: " + repository)

    # Git clone repository
    # TODO: Use git_repository if possible instead
    index_repository_root = "{name}_index_repo".format(name=ctx.attr.name)
    result = ctx.execute(["git", "clone", repository, index_repository_root])
    if result.return_code != 0:
        fail("Unable to clone index repository", repository)
    print("Index cloned")

    ctx.file("BUILD", "filegroup(name='{name}',srcs=[])".format(name=ctx.attr.name), executable=False)

_cargo_repo_index = repository_rule(
    attrs = {
        "repository": attr.string(
            default = "https://github.com/rust-lang/crates.io-index",
        ),
    },
    implementation = _cargo_repo_index_impl,
)

_cargo_repository = repository_rule(
    attrs = {
        "crate": attr.string(
            mandatory = True,
        ),
        "version": attr.string(
            mandatory = True,
        ),
        "repo_target": attr.label(
            mandatory = True,
        ),
        "repository": attr.string(
            default = "https://github.com/rust-lang/crates.io-index",
        ),
        "_java_bin": attr.label(
            default = Label("@local_jdk//:bin/java"),
        ),
        "_cargo_dependency_resolver": attr.label(
            allow_files = True,
            default = Label("//:cargo_dependency_resolver.py"),
        ),
        "_java_cargo_dependency_resolver": attr.label(
            allow_files = True,
            default = Label("//:semver_test.jar"),
        ),
        "_crate_root_finder": attr.label(
            allow_files = True,
            default = Label("//:cargo_crate_root_finder"),
        ),
        "sha256hashes": attr.string_dict(
            default = {} # { "time-0.1.2": "723498bj5nbjk34btbcu9hda9s0j2309rj23f9n23nv9" },
        ),
    },
    implementation = _cargo_repository_impl,
)

def cargo_repository(name=None,repository=None, **kwargs):
    cargo_repo_index_name = "{name}__index".format(name=name)
    _cargo_repo_index(name=cargo_repo_index_name, repository=repository)
    _cargo_repository(name=name, repository=repository, repo_target="@{name}//:{name}".format(name=cargo_repo_index_name), **kwargs)