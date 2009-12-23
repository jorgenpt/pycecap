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

import weakref

class Network(object):
    def __init__(self, network, info, old_me=None):
        self.network = network
        self.info = info

        if old_me is not None:
            self.gateways = old_me.gateways
        else:
            self.gateways = []

    def __repr__(self):
        return 'Network(%r, %r, <gateways=%r>)' % (self.network, self.info, self.gateways)

class Connection(object):
    def __init__(self, network_or_dict, mypresence=None):
        if mypresence is None:
            self.network = network_or_dict.pop('network')
            self.mypresence = network_or_dict.pop('mypresence')
        else:
            self.network = network_or_dict
            self.mypresence = mypresence

    def __hash__(self):
        return hash((self.network, self.mypresence))

    def __cmp__(self, other):
        if type(self) != type(other):
            return cmp(type(self), type(other))
        return cmp((self.network, self.mypresence), (self.network, other.mypresence))

    def __repr__(self):
        return 'Connection(%r, %r)' % (self.network, self.mypresence)

class LocalPresence(object):
    def __init__(self, connection, info, old_me=None):
        self.connection = connection
        self.info = info

        if old_me is not None:
            self.channels = old_me.channels
            self.presences = old_me.presences
        else:
            self.channels = {}
            self.presences = {}

    def get_channel(self, channel):
        if channel not in self.channels:
            self.channels[channel] = Channel(self, channel, {})
        return self.channels[channel]

    def get_presence(self, presence):
        if presence not in self.presences:
            self.presences[presence] = Presence(self, presence, {})
        return self.presences[presence]

    def __repr__(self):
        return 'LocalPresence(%r, %r, <channels=%r, presences=%r>)' % (self.connection, self.info, self.channels, self.presences)

class LocalPresenceObject(object):
    def __init__(self, local_presence, name, info):
        self.local_presence = weakref.ref(local_presence)
        self.name = name
        self.info = info

    def reparent(self, new_lp):
        self.local_presence = weakref.ref(new_lp)

class Presence(LocalPresenceObject):
    def __init__(self, local_presence, name, info, old_me=None):
        super(Presence, self).__init__(local_presence, name, info)

        if old_me is not None:
            self.channels = old_me.channels
        else:
            self.channels = set()

    def __repr__(self):
        return 'Presence(%r, %r, %r, <channels=%r>)' % (self.local_presence().connection, self.name, self.info, self.channels)

class Channel(LocalPresenceObject):
    def __init__(self, presence, name, info, old_me=None):
        super(Channel, self).__init__(local_presence, name, info)

        if old_me is not None:
            self.presences = old_me.presences
        else:
            self.presences = {}

    def __repr__(self):
        return 'Channel(%r, %r, %r, <presences=%r>)' % (self.local_presence().connection, self.name, self.info, self.presences)
