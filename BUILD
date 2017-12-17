load("@subpar//:subpar.bzl",
    "par_binary",
)
load("@pip_requirements//:requirements.bzl", "all_requirements")

par_binary(
    name = "cargo_dependency_resolver",
    srcs = [
        "cargo_dependency_resolver.py",
    ],
    deps = all_requirements,
)

par_binary(
    name = "cargo_crate_root_finder",
    srcs = [
        "cargo_crate_root_finder.py",
    ],
    deps = all_requirements,
)

java_binary(
    name = "semver_test",
    srcs = [ "SemverMain.java", ],
    deps = [
        "@jsemver//jar",
        "@com_google_code_gson_gson//jar",
        "@semver4j//:jar",
    ],
    main_class = "SemverMain",
)