#!/usr/bin/python

import pycecap

from sys import stdin, stderr
from pprint import pprint

client = pycecap.StateKeeper()

lineno = 0
for line in stdin:
    lineno = lineno + 1

    try:
        line = line.rstrip('\n\r')
        dir, message = line[:1], line[1:]

        if not message:
            continue

        if dir == '<':
            client.parse(message)
        else:
            command = pycecap.Command(message)
            client._next_tag = int(command.tag)
            client.presend(command)
    except:
        print >>stderr, "Crashed on input line %i" % lineno
        raise

pprint(client.__dict__)
