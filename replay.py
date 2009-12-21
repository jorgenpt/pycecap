#!/usr/bin/python

import client
from sys import stdin

from pprint import pprint

c = client.Client()

for line in stdin:
    line = line.rstrip('\n\r')
    dir, message = line[:1], line[1:]

    if dir == '<':
        c.parse(message)
    else:
        c.presend(client.protocol.Command(message))

pprint(c.__dict__)
