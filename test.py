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

log_name = 'logs/replay-%i.log' % os.getpid()

def work(c, icecap, replay):
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

dir_name = os.path.dirname(log_name)
if not os.path.isdir(dir_name):
    os.makedirs(dir_name)
replay = open(log_name, 'w')

try:
    while work(c, icecap, replay):
        pass
except Exception, e:
    print e
finally:
    replay.close()
    icecap.terminate()
    pprint(c.__dict__)
    print 'Wrote replaylog to %s' % log_name
