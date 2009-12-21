#!/usr/bin/python

# Simple test-code to test parsing of data.
# Very dirty, but quick way of seeing if things are hooked
# up like they should be.

import client

import os
from pprint import pprint
import select
import subprocess
from sys import stdin

def doWork(c, icecap, replay):
    rlist = [stdin, icecap.stdout]
    try:
        ready, _, _ = select.select(rlist, [], [])
    except select.error:
        return False
    except KeyboardInterrupt:
        return False

    for r in ready:
        line = r.readline().rstrip('\n\r')
        if r == stdin:
            if line == 'dump':
                pprint(c.__dict__)
            elif line == 'quit' or line == 'exit':
                return False
            else:
                print >>replay, '>%s' % line
                try:
                    c.fakesend(line)
                    print '> %s' % line
                    icecap.stdin.write(line + '\n')
                except client.protocol.InvalidMessageException:
                    print 'Invalid message'
        else:
            print >>replay, '<%s' % line
            print '< %s' % line
            c.parse(line)

    return True


c = client.Client()
icecap = subprocess.Popen(['ssh', 'arach', 'icecapd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

if not os.path.isdir('logs'):
    os.mkdir('logs')
replay = open('logs/replay-%i.log' % os.getpid(), 'w')

try:
    while doWork(c, icecap, replay):
        pass
except Exception, e:
    print e
finally:
    replay.close()
    icecap.terminate()
    pprint(c.__dict__)
