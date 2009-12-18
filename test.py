#!/usr/bin/python

# Simple test-code to test parsing of data.
# Very dirty, but quick way of seeing if things are hooked
# up like they should be.

import client
from sys import stdin

from pprint import pprint

c = client.Client()

for line in stdin:
    line = line.rstrip('\n\r')
    dir, message = line[:5], line[5:]

    if dir == 'recv:':
        c.parse(message)
    else:
        c.fakesend(message)

pprint(c.__dict__)
