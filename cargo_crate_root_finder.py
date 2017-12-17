import json
import os
import re
import sys
import toml

MEMBERS_LINE_PREFIX = 'members = '
MEMBERS_LINE_PREFIX_LEN = len(MEMBERS_LINE_PREFIX)

def perror(msg):
    print >> sys.stderr, str(msg)

def parse_section(section):
    # print 'Section: ' + section
    # perror(section)
    parsed_section = {}
    for line in section.split('\n'):
        line = line.strip()
        if line == '' or line.startswith('#'):
            continue
        line_parts = line.split('=', 1)
        if len(line_parts) != 2:
            perror('Bad line: ' + line)
        parsed_section[line_parts[0].strip()] = line_parts[1].strip()
    return parsed_section
    # compressed = [ [v.strip() for v in attribute_line.split('=', 1)]
    #             for attribute_line in
    #                 (attribute_line.strip() for attribute_line in section.split('\n'))
    #                     if (attribute_line != '' or not attribute_line.startswith('#')) ]
    # perror(compressed)
    # parsed_section = dict(compressed)
    # print parsed_section
    return parsed_section['path'].strip('"') if 'path' in parsed_section else None

def main(args):
    crate_root = args[1]
    crate = args[2]

    cargo_toml_path = os.path.join(crate_root, 'Cargo.toml')
    assert os.path.exists(cargo_toml_path)

    cargo_toml = toml.load(cargo_toml_path)

    print 'path ' + cargo_toml.get('lib', {}).get('path', '')
    features = cargo_toml.get('features', {}).get('default', [])
    print 'features ' + ' '.join(f.strip('\r\n\t ') for f in features)
    return
    print(cargo_toml)
    #

    with open(cargo_toml, 'r') as f:
        cargo_toml_contents = f.read()

    section_list = [s.strip() for s in re.split('(\[+.+\]+)', cargo_toml_contents) if s.strip() != '']
    sections = zip(section_list[::2], section_list[1::2])

    in_lib = False
    in_features = False
    for section in section_list:
        if in_lib:
            parsed_section = parse_section(section)

            if 'path' in parsed_section:
                print 'path ' + parsed_section['path'].strip('"')

            in_lib = False
        elif in_features:
            parsed_section = parse_section(section)

            features = { 'default' }
            final_features = set()
            while len(features) > 0:
                feature = features.pop()
                if feature in parsed_section:
                    perror('!!!' + str(crate) + " = " + str(feature) + ': ' + str(parsed_section[feature]))
                    feature_deps = json.loads(parsed_section[feature])
                    features.extend(feature_deps)
                    final_features.extend(feature_deps)

                print 'features ' + ' '.join(final_features)

            in_features = False
        if section == '[lib]':
            in_lib = True
        elif section == '[features]':
            in_features = True

    return

    ready_for_members = False
    for line in lines:

        if ready_for_members:
            if line.startswith(MEMBERS_LINE_PREFIX):
                #print 'members line found'
                members_list = line[MEMBERS_LINE_PREFIX_LEN:]
                members = json.loads(members_list)
                #print members
                for member in members:
                 #   print 'checking member: ' + member
                    if os.path.basename(member) == crate:
                        print member
                        return
        if line.strip() == '[workspace]':
            #print 'workspace found'
            ready_for_members = True

if __name__ == '__main__':
    main(sys.argv)