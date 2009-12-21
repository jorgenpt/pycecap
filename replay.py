#!/usr/bin/python

import client
from sys import stdin

from pprint import pprint

c = client.Client()

for line in stdin:
    line = line.rstrip('\n\r')
    dir, message = line[:1], line[1:]

    if not message:
        continue

    if dir == '<':
        c.parse(message)
    else:
        command = client.protocol.Command(message)
        c._next_tag = int(command.tag)
        c.presend(command)

pprint(c.__dict__)
