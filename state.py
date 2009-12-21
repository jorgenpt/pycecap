#!/usr/bin/python
# vim: set fileencoding=utf-8 :
# 
# pycecap
# Copyright (c) 2009 Jørgen Tjernø <jorgenpt@gmail.com>
#
# This package is free software;  you can redistribute it and/or
# modify it under the terms of the license found in the file
# named COPYING that should have accompanied this file.
#
# THIS PACKAGE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

class Network(dict):
    def __init__(self, params={}, old_network=None):
        super(Network, self).__init__(params)

        if old_network is None:
            self.gateways = []
            self.presences = {}
        else:
            self.gateways = old_network.gateways
            self.presences = old_network.presences

    def __repr__(self):
        return 'Network(params=%s, gateways=%r, presences=%r)' % (super(Network, self).__repr__(), self.gateways, self.presences)

class LocalPresence(dict):
    def __init__(self, params={}, old_presence=None):
        super(LocalPresence, self).__init__(params)

        if old_presence is None:
            self.channels = {}
        else:
            self.channels = old_presence.channels

    def __repr__(self):
        return 'LocalPresence(params=%s, channels=%r)' % (super(LocalPresence, self).__repr__(), self.channels)

class Channel(dict):
    def __init__(self, params={}, old_network=None):
        super(Channel, self).__init__(params)

        if old_network is None:
            self.presences = []
        else:
            self.presences = old_network.presences

    def __repr__(self):
        return 'Channel(params=%s, presences=%r)' % (super(Channel, self).__repr__(), self.presences)
