import json
import os
import re
import semver
import sys

def eprint(msg):
    print >> sys.stderr, str(msg)

def crate_to_path(crate):
    name_len=len(crate)

    path = None
    if name_len == 1:
        path = ['1', crate]
    elif name_len == 2:
        path = ['2', crate]
    elif name_len == 3:
        path = ['3', crate[0], crate]
    else:
        path = [crate[0:2], crate[2:4], crate]

    return os.path.join(*path)

def assert_eq(a, b):
    assert a == b, str(a) + " != " + str(b)

def assert_true(a):
    assert_eq(a, True)

def assert_false(a):
    assert_eq(a, False)

def test_crate_to_path():
    assert_eq(crate_to_path("a"), "1/a")
    assert_eq(crate_to_path("ab"), "2/ab")
    assert_eq(crate_to_path("aac"), "3/a/aac")
    assert_eq(crate_to_path("atty"), "at/ty/atty")
    assert_eq(crate_to_path("apples"), "ap/pl/apples")

def try_convert(v, t):
    try:
        return t(v)
    except:
        return v

def semver_compare(semver_a, semver_b):
    # return semver.compare(semver_a, semver_b)

    int_split = lambda s: [try_convert(v, int) for v in s.split('.')]
    a_parts = int_split(semver_a)
    b_parts = int_split(semver_b)

    while len(a_parts) < len(b_parts):
        c = '*' if a_parts[-1] == '*' else 0
        a_parts.append(c)

    while len(b_parts) < len(a_parts):
        c = '*' if b_parts[-1] == '*' else 0
        b_parts.append(c)

    for i in xrange(len(a_parts)):
        a = a_parts[i]
        b = b_parts[i]

        if a == '*' or b == '*':
            continue
        elif a > b:
            return 1
        elif a < b:
            return -1
    return 0

def test_semver_compare():
    assert_eq(semver_compare("1", "1"), 0)
    assert_eq(semver_compare("1.0.0", "1"), 0)
    assert_eq(semver_compare("1", "*"), 0)
    assert_eq(semver_compare("1.0", "*"), 0)
    assert_eq(semver_compare("1.0.0.alpha", "*"), 0)
    assert_eq(semver_compare("1.2.3", "1.*"), 0)
    assert_eq(semver_compare("1", "2"), -1)
    assert_eq(semver_compare("2", "1"), 1)
    assert_eq(semver_compare("1.0.0", "1.2"), -1)
    assert_eq(semver_compare("123", "1.234"), 1)
    assert_eq(semver_compare("123", "1.234"), 1)


def semver_cap(semver):
    int_split = lambda s: [try_convert(v, int) for v in s.split('.')]
    version = int_split(semver)

    rollover = False
    for i in xrange(len(version)):
        if rollover:
            version[i] = 0
        else:
            v = version[i]
            if v != 0:
                assert isinstance(v, int), "Attempting to get a version cap for a non-numeric version"
                version[i] += 1
                rollover = True

    # Case with "^0.0" or "^0"
    if not rollover:
        version[-1] = 1

    return '.'.join(str(v) for v in version)

def test_semver_cap():
    assert_eq(semver_cap('1'), '2')
    assert_eq(semver_cap('1.0.0'), '2.0.0')
    assert_eq(semver_cap('1.2.3'), '2.0.0')
    assert_eq(semver_cap('0.0.1'), '0.0.2')
    assert_eq(semver_cap('0.1.2'), '0.2.0')
    assert_eq(semver_cap('0.1.2.alpha'), '0.2.0.0')
    assert_eq(semver_cap('0.0'), '0.1')
    assert_eq(semver_cap('1.0.20'), '2.0.0')

def version_match(actual, requirement):
    # if '.' not in actual and '*' not in actual:
    #     actual += '.0.0'
    return semver.satisfies(actual, requirement)
    if not re.match('[<>=!].*', requirement):
        requirement = '== ' + requirement
    return semver.match(actual, requirement)
    ## SEMVER!!
    return (
        requirement == actual or
        (
            requirement[0] == '^' and
            semver_compare(actual, requirement[1:]) >= 0 and # Above requirement
            semver_compare(actual, semver_cap(requirement[1:])) < 0 # but below rollover
        ) or
        (
            requirement.startswith('> ') and
            semver_compare(actual, requirement[2:]) > 0
        ) or
        (
            requirement.startswith('>= ') and
            semver_compare(actual, requirement[3:]) >= 0
        ) or
        (
            requirement.startswith('= ') and
            semver_compare(actual, requirement[2:]) == 0
        ) or
        (
            requirement.startswith('<= ') and
            semver_compare(actual, requirement[3:]) <= 0
        ) or
        (
            requirement.startswith('< ') and
            semver_compare(actual, requirement[2:]) < 0
        ) or
        semver_compare(actual, requirement) == 0
    )

def test_version_match():
    assert_true(version_match('0.0.1', '*'))
    assert_true(version_match('2.0.3-alpha1', '*'))
    assert_true(version_match('1.0.0', '*'))
    assert_true(version_match('1.0.0', '^1'))
    assert_true(version_match('1.0.0', '^1.0'))
    assert_true(version_match('1.4', '^1.2.3'))
    assert_true(version_match('1.9.9.9', '^1.0'))
    assert_true(version_match('1.9.9.9-extra', '^1.0'))

    assert_false(version_match('2.0.0', '^1.0'))
    assert_false(version_match('2.0.0', '^1'))

def resolve(index, crate, requirements, dep_set=None):
    """
    index - The path to the index
    crate - The name of the crate
    version - The version of the crate
    """
    if dep_set is None:
        dep_set = set()

    eprint("finding crate: " + crate)
    crate_path_in_index = crate_to_path(crate)
    crate_info_file = os.path.join(index, crate_path_in_index)

    requirement_list = [r.strip() for r in requirements.split(',')]

    with open(crate_info_file, 'r') as ci:
        for line in ci.readlines()[::-1]: # Use the newest versions first (always appended by cargo so newest on the bottom)
            version_blob = json.loads(line)
            version = version_blob['vers']
            if all(version_match(version, requirement) for requirement in requirement_list):
                key = (crate, version)

                # Skip it if we already have it to avoid a cyclical dependency
                if key in dep_set:
                    eprint("cycle found. Depset: " + str(dep_set))
                    continue

                deps = version_blob['deps']
                ret = { key: { dep['name']: dep for dep in deps } }
                abort_version = False
                for dep in deps:
                    dep_name = dep['name']
                    if dep['kind'] != 'normal' or dep['optional']:
                        continue
                    resolved_dep, resolved_version = resolve(index, dep_name, dep['req'], dep_set | set([key]))
                    if resolved_dep is None:
                        eprint('Unable to resolve dep: ' + json.dumps(dep))
                        # This is fine. maybe we can work with the next version
                        abort_version = True
                        break
                    else:
                        # make this a name-keyed dict instead of a list
                        ret[key][dep_name]['__resolved_version'] = resolved_version
                        ret.update(resolved_dep)
                # One of the dependencies couldn't be resolved, move on to the next
                if not abort_version:
                    return ret, version
    eprint('Unable to find ' + crate + ' version ' + requirements)
    return None

def main(args):
    root_crate_name = args[1]
    root_crate_version = args[2]
    crate_index_repo = args[3]

    eprint("Finding {name}-{version} in {repo}".format(name=root_crate_name, version=root_crate_version, repo=crate_index_repo))
    crate_path_in_index = crate_to_path(root_crate_name)
    eprint("Relative path for {name} is {path}".format(name=root_crate_name, path=crate_path_in_index))

    deps, _ = resolve(crate_index_repo, root_crate_name, root_crate_version)

    # eprint(deps)
    # cargo 2.2.0 crate 2.3 rust 3.4 io 3.1
    # crate 2.3
    # rust 3.4 io 3.1o
    for (crate, version), dep_map in deps.iteritems():
        print ' '.join(
            [crate, version] +
            [ dep_name + ' ' + dep_info['__resolved_version'] + ' ' + ':'.join(dep_info.get('features', []))
                for dep_name, dep_info in dep_map.iteritems() if '__resolved_version' in dep_info
            ])
  #      print deps
#        dep_list = [dep['name'] + ':' + dep['__resolved_version'] for dep in deps]
 #       print "{name} {version} {deps}".format(name = key[0], version = key[1], deps = ','.join(dep_list))
  #  print json.dumps(deps)
    # Parse for version

    # Grab deps

    # Print deps

    # Go back to search for deps

if __name__ == '__main__':
    test_crate_to_path()
    test_semver_compare()
    test_semver_cap()
    test_version_match()
    main(sys.argv)