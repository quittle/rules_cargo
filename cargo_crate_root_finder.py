import json
import os
import re
import sys

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

    cargo_toml = os.path.join(crate_root, 'Cargo.toml')
    assert os.path.exists(cargo_toml)

    with open(cargo_toml, 'r') as toml:
        cargo_toml_contents = toml.read()

    section_list = [s.strip() for s in re.split('(\[+.+\]+)', cargo_toml_contents) if s.strip() != '']
    sections = zip(section_list[::2], section_list[1::2])

    in_lib = False
    in_features = False
    for section in section_list:
        if in_lib:
            parsed_section = parse_section(section)
            if 'path' in parsed_section:
                # print 'path ' +
                print parsed_section['path'].strip('"')
            in_lib = False
        elif in_features:
            parsed_section = parse_section(section)
            if 'default' in parsed_section:
                pass
                # print 'features ' + ' '.join(json.loads(parsed_section['default']))

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