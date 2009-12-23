#!/usr/bin/python

import client
from sys import stdin

from pprint import pprint

c = client.Client()

lineno = 0
for line in stdin:
    lineno = lineno + 1

    try:
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
    except:
        print "Crashed on input line %i" % lineno

pprint(c.__dict__)
