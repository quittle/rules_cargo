# Copyright (c) 2017 Dustin Toff
# Licensed under Apache License v2.0

workspace(name = "rules_cargo")

# Build script dependencies
maven_jar(
    name = "jsemver",
    artifact = "com.github.zafarkhaja:java-semver:0.9.0",
    sha1 = "59a83ca73c72a5e25b3f0b1bb305230a11000329",
)

SEMVER4J_BUILD_FILE = """

java_library(
    name = "jar",
    srcs = glob(["src/main/**/*.java"]),
    visibility = [ "//visibility:public" ],
)

"""

new_git_repository(
    name = "semver4j",
    remote = "https://github.com/vdurmont/semver4j",
    commit = "d2c6c35641e72c9ce1f7cdebcbb4cf06f1c52d01",
    build_file_content = SEMVER4J_BUILD_FILE,
)

maven_jar(
    name = "z_semver4j",
    artifact = "com.vdurmont:semver4j:2.1.0",
    sha1 = "f4123dbb6a2d7991eff772e9a4d8f4111dac8e55",
)

maven_jar(
    name = "com_google_code_gson_gson",
    artifact = "com.google.code.gson:gson:2.8.2",
    sha1 = "3edcfe49d2c6053a70a2a47e4e1c2f94998a49cf",
)

git_repository(
    name = "subpar",
    remote = "https://github.com/google/subpar",
    commit = "5e90e97bc1e8dd88dedd56f5e2e10fab4dba93bd", # 1.1.0
)
git_repository(
    name = "io_bazel_rules_python",
    remote = "https://github.com/bazelbuild/rules_python",
    commit = "346b898e15e75f832b89e5da6a78ee79593237f0",
)
load("@io_bazel_rules_python//python:pip.bzl", "pip_import")

pip_import(
    name = "pip_requirements",
    requirements = "//:requirements.txt",
)
load("@pip_requirements//:requirements.bzl", "pip_install")
pip_install()

# Actual repository rule dependencies
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

load("//:cargo.bzl", "cargo_repository")

cargo_repository(
    name = "cargo",
    crate = "cargo",
    version = "0.22.0",
    sha256hashes = {
        "libgit2-sys-0.6.0": "f73b0f0fe922fe6cacd208645b42ddbbd24dbbb8d1ad1de0e0e28761c678e3e4",
    },
)

cargo_repository(
    name = "url",
    crate = "url",
    version = "1.6.0",
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