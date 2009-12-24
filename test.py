#!/usr/bin/python

# Simple test-code to test parsing of data.
# Very dirty, but quick way of seeing if things are hooked
# up like they should be.

import pycecap 

import os
from pprint import pprint
import select
import subprocess
from sys import stdin

log_name = 'logs/replay-%i.log' % os.getpid()

def work(client, icecap, replay):
    rlist = [stdin, icecap.stdout]
    try:
        ready, _, _ = select.select(rlist, [], [])
    except select.error:
        return False
    except KeyboardInterrupt:
        return False

    for r in ready:
        line = r.readline().rstrip('\n\r')
        if not line:
            continue

        if r == stdin:
            if line == 'dump':
                pprint(client.__dict__)
            elif line == 'quit' or line == 'exit':
                return False
            else:
                try:
                    command = client.presend(pycecap.Command(line))
                    print >>replay, '>%s' % command
                    print '> %s' % command
                    icecap.stdin.write(str(command) + '\n')
                except pycecap.InvalidMessageException:
                    print 'Invalid message'
        else:
            print >>replay, '<%s' % line
            print '< %s' % line
            client.parse(line)

    return True


client = pycecap.StateKeeper()
icecap = subprocess.Popen(['ssh', 'arach', 'icecapd'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

dir_name = os.path.dirname(log_name)
if not os.path.isdir(dir_name):
    os.makedirs(dir_name)
replay = open(log_name, 'w')

try:
    while work(client, icecap, replay):
        pass
finally:
    replay.close()
    icecap.terminate()
    pprint(client.__dict__)
    print 'Wrote replaylog to %s' % log_name
