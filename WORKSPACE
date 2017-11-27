# Copyright (c) 2017 Dustin Toff
# Licensed under Apache License v2.0

workspace(name = "rules_cargo")

_rust_commit = "e5ec8bef453fdc496551731c5b82ca9598bed382"
http_archive(
    name = "io_bazel_rules_rust",
    sha256 = "b907dd2b5c787afd245701eb7a1247ea0992d45ae15afe05279d48c30fc321ec",
    strip_prefix = "rules_rust-{commit}".format(commit = _rust_commit),
    urls = [
        # "http://bazel-mirror.storage.googleapis.com/github.com/bazelbuild/rules_rust/archive/0.0.5.tar.gz",
        "https://github.com/bazelbuild/rules_rust/archive/{commit}.tar.gz".format(commit = _rust_commit),
    ],
)
# git_repository(
#     name = "io_bazel_rules_rust",
#     remote = "https://github.com/bazelbuild/rules_rust.git",
#     branch = "master",
# )
load("@io_bazel_rules_rust//rust:repositories.bzl", "rust_repositories")
rust_repositories()

new_local_repository(
    name = "fake",
    path = ".",
    build_file_content = "",
)

load("//:cargo.bzl", "cargo_repository")

cargo_repository(
    name = "cargo",
    crate = "cargo",
    version = "0.22.0",
    sha256hashes = {
        "libgit2-sys-0.6.0": "f73b0f0fe922fe6cacd208645b42ddbbd24dbbb8d1ad1de0e0e28761c678e3e4",
    },
)

#local_cargo_repository(
#    name = "cargo",
#    path = "cargo_srcs/cargo-0.22.0",
#)

# new_local_repository(
#     name = "cargo",
#     path = "cargo_srcs/cargo-0.22.0",
#     build_file_content = """
# load("@io_bazel_rules_rust//rust:rust.bzl",
#     "rust_binary",
# )

# rust_binary(
#     name = "cargo",
#     srcs = glob(["src/**/*.rs",]),
#     crate_root = "src/cargo/lib.rs",
#     deps = [],
# )
#     """
# )