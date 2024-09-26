#!/usr/bin/env python3
'''
Convert tables in nips README.md to machine-readable JSON format.

Usage: python3 read_nips_tables.py <path to NIPS repository>
'''
# laanwj 2024
# SPDX-License-Identifier: MIT
import re

def parse_md_table(lines, start_idx):
    idx = start_idx
    headers = []
    rows = []
    while lines[idx] != "":
        cols = [c.strip() for c in lines[idx].split('|')]
        cols = cols[1:-1]
        if (idx - start_idx) == 0:
            headers = cols
        elif (idx - start_idx) == 1:
            if any([set(c) != {'-'} for c in cols]):
                raise ValueError('Invalid row after header row')
        else:
            rows.append(cols)
        idx += 1

    return (headers, rows, idx)

def parse_range(col):
    # single nip
    m = re.fullmatch('`([0-9]+)`', col)
    if m:
        return int(m.group(1)), int(m.group(1))

    # range (`<begin>`-`<end>` or `<begin>-<end>` syntax)
    m = re.fullmatch('`([0-9]+)`-`([0-9]+)`', col)
    if not m:
        m = re.fullmatch('`([0-9]+)-([0-9]+)`', col)
    if m:
        begin = m.group(1)
        end = m.group(2)
        if len(end) < len(begin): # end only specifies part of digits
            end = begin[0:-len(end)] + end
        return int(begin), int(end)

    raise ValueError('invalid NIP range')

def parse_nips_column(col):
    nips = []

    for ref in col.split(','):
        m = re.fullmatch(r'\[([0-9]+)\]\(([0-9]+).md\)', ref.strip())
        if m and m.group(1) == m.group(2):
            nips.append(int(m.group(1)))

        m = re.fullmatch(r'(?:\[.*\])?\[(.*)\]', ref.strip())
        if m:
            nips.append(m.group(1))

    return nips

def parse_nips_list(lines):
    '''
    Parse the list of nips links.
    '''
    idx = lines.index('## List')
    idx += 1

    while lines[idx] == "" or lines[idx][0] != '-': # skip to list
        idx += 1

    nips = []
    while lines[idx] != "" and lines[idx][0] == '-':
        m = re.fullmatch(r'- \[(.*?)\]\(([0-9]+)\.md\)(?: --- (.*))?', lines[idx])
        nips.append({
            'nip': int(m.group(2)),
            'description': m.group(1),
            'deprecation_notice': m.group(3),
        })
        idx += 1

    return nips

def parse_kinds_table(lines):
    '''
    Parse "Event kinds" table.
    '''
    idx = lines.index('## Event Kinds')
    idx += 1

    while lines[idx] == "" or lines[idx][0] != '|': # skip to table
        idx += 1
    headers, rows, idx = parse_md_table(lines, idx)

    if headers != ['kind', 'description', 'NIP']:
        raise ValueError('Kinds table has unknown columns')

    kinds = []
    for row in rows:
        kinds.append({
            'range': list(parse_range(row[0])),
            'description': row[1],
            'nips': parse_nips_column(row[2]),
        })

    return kinds

def parse_messages_table(lines, title):
    '''
    Parse "Client to Relay" and "Relay to Client" table.
    '''
    idx = lines.index(title)
    idx += 1

    while lines[idx] == "" or lines[idx][0] != '|': # skip to table
        idx += 1
    headers, rows, idx = parse_md_table(lines, idx)

    if headers != ['type', 'description', 'NIP']:
        raise ValueError('Messages table has unknown columns')

    messages = []
    for row in rows:
        if row[0][0] != '`' or row[0][-1] != '`':
            raise ValueError('Invalid message type in messages table')
        mtype = row[0][1:-1]
        messages.append({
            'type': mtype,
            'description': row[1],
            'nips': parse_nips_column(row[2]),
        })

    return messages

def parse_tags_table(lines):
    '''
    Parse "Standardized Tags" table.
    '''
    idx = lines.index('## Standardized Tags')
    idx += 1

    while lines[idx] == "" or lines[idx][0] != '|': # skip to table
        idx += 1
    headers, rows, idx = parse_md_table(lines, idx)

    if headers != ['name', 'value', 'other parameters', 'NIP']:
        raise ValueError('Tags table has unknown columns')

    tags = []
    for row in rows:
        if row[0][0] != '`' or row[0][-1] != '`':
            raise ValueError('Invalid tag in tags table')
        tag = row[0][1:-1]

        if row[1] != '--':
            # fix up some parsing problems
            row[1] = row[1].replace('URL, etc', 'URL etc')
            row[1] = row[1].replace('millisatoshis, stringified', 'millisatoshis (stringified)')

            parameters = [p.strip() for p in row[1].split(',')]
        else:
            parameters = []

        if row[2] != '--':
            other_parameters = [p.strip() for p in row[2].split(',')]
        else:
            other_parameters = []

        tags.append({
            'tag': tag,
            'required_parameters': parameters,
            'other_parameters': other_parameters,
            'nips': parse_nips_column(row[3]),
        })

    return tags

def parse_nips_tables(filename):
    with open(filename, 'r') as f:
        lines = [l.rstrip() for l in f.readlines()]

    nips = parse_nips_list(lines)
    kinds = parse_kinds_table(lines)
    messages_to_relay = parse_messages_table(lines, '### Client to Relay')
    messages_to_client = parse_messages_table(lines, '### Relay to Client')
    tags = parse_tags_table(lines)

    return nips, kinds, messages_to_relay, messages_to_client, tags

if __name__ == '__main__':
    import json, os, sys
    nips, kinds, messages_to_relay, messages_to_client, tags = parse_nips_tables(os.path.join(sys.argv[1], 'README.md'))
    os.makedirs('json', exist_ok=True)
    with open('json/nips.json', 'w') as f:
        json.dump(nips, f, indent=4)
    with open('json/kinds.json', 'w') as f:
        json.dump(kinds, f, indent=4)
    with open('json/messages_to_relay.json', 'w') as f:
        json.dump(messages_to_relay, f, indent=4)
    with open('json/messages_to_client.json', 'w') as f:
        json.dump(messages_to_client, f, indent=4)
    with open('json/tags.json', 'w') as f:
        json.dump(tags, f, indent=4)
