#!/usr/bin/python

# Simple test-code to test parsing of data.
# Very dirty, but quick way of seeing if things are hooked
# up like they should be.

import client
from sys import stdin

import select
from pprint import pprint
import subprocess

c = client.Client()
icecap = subprocess.Popen(['ssh', 'arach', 'icecapd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

while True:
    rlist = [stdin, icecap.stdout]
    try:
        ready, _, _ = select.select(rlist, [], [])
    except select.error:
        break
    except KeyboardInterrupt:
        break

    for r in ready:
        line = r.readline().rstrip('\n\r')
        if r == stdin:
            if line == 'dump':
                pprint(c.__dict__)
            elif line == 'quit' or line == 'exit':
                break
            else:
                try:
                    c.fakesend(line)
                    print '> %s' % line
                    icecap.stdin.write(line)
                except client.protocol.InvalidMessageException:
                    print 'Invalid message'
        else:
            print '< %s' % line
            c.parse(line)

icecap.terminate()
pprint(c.__dict__)
