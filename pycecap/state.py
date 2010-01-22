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

'''A set of classes to represent the state of an icecap session.'''

import weakref

class Network(object):
    '''This is just a name and a set of gateways to connect to that network.'''

    def __init__(self, network, info, old_me=None):
        '''Create a new network.

        Args:
            network: Name of the network.
            info: Dict of arbitrary information about the network (from e.g. a 'network list' reply)
            old_me: Optional argument, if present - should be a Network that we copy gateways from.
        '''

        self.network = network
        self.info = info

        if old_me is not None:
            self.gateways = old_me.gateways
        else:
            self.gateways = []

    def __repr__(self):
        return 'Network(%r, %r, <gateways=%r>)' % (self.network, self.info, self.gateways)

class Connection(object):
    '''This is a (unique) mypresence/network name pair (identifier) representing a connection to a service (e.g. IRC).
    
    This is similar to a two-tuple - it hashes and compares properly, so it can be used as a hash key or in a set.
    '''

    def __init__(self, network_or_dict, mypresence=None):
        '''Create a new connection identifier.

        Args:
            network_or_dict: Name of the network, or if mypresence is None, a dict containing
                the 'network' and 'mypresence' keys.
            mypresence: Optional argument, if present - should be the name of the local presence.
        '''

        if mypresence is None:
            self.network = network_or_dict['network']
            self.mypresence = network_or_dict['mypresence']
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
    '''This is all the information associated with a Connection.'''

    def __init__(self, connection, info, old_me=None):
        '''Create a new local presence.

        Args:
            connection: A Connection object identifying this LocalPresence
            info: Dict of arbitrary information about the network (from e.g. a 'presence list' reply)
            old_me: Optional argument, if present - should be a LocalPresence that we copy
                channels & presences from.
        '''

        self.connection = connection
        self.info = info

        if old_me is not None:
            self.channels = old_me.channels
            self.presences = old_me.presences
        else:
            self.channels = {}
            self.presences = {}

    def get_channel(self, channel):
        '''Get a Channel object for the given channel name.

        If a Channel of the given name is known, it's returned. Otherwise,
        if no Channel is found, it creates a new, empty Channel object and
        associates it with the given name, then returns this object.

        Args:
            channel: Name of the channel you want to retrieve.
        '''

        if channel not in self.channels:
            self.channels[channel] = Channel(self, channel, {})
        return self.channels[channel]

    def get_presence(self, presence):
        '''Get a Presence object for the given presence name.

        If a Presence of the given name is known, it's returned. Otherwise,
        if no Presence is found, it creates a new, empty Presence object and
        associates it with the given name, then returns this object.

        Args:
            presence: Name of the presence you want to retrieve.
        '''

        if presence not in self.presences:
            self.presences[presence] = Presence(self, presence, {})
        return self.presences[presence]

    def __repr__(self):
        return 'LocalPresence(%r, %r, <channels=%r, presences=%r>)' % (self.connection, self.info, self.channels, self.presences)

class LocalPresenceObject(object):
    '''This represents some kind of data associated with a LocalPresence.

    LocalPresenceObject is the parent class for classes that represent information
    that's associated with one (and only one) LocalPresence (Connection). It takes
    care of knowing which LocalPresence that is, and reparenting if needed.
    '''

    def __init__(self, local_presence, name, info):
        '''Create a new local presence info blob.

        Args:
            local_presence: The LocalPresence we belong to.
            name: The name of this info blob.
            info: Dict of arbitrary information about the network (from e.g. a 'presence list' reply)
        '''

        self.local_presence = weakref.ref(local_presence)
        self.name = name
        self.info = info

    def reparent(self, new_lp):
        '''Reparent this info blob to belong to a different LocalPresence object.'''

        self.local_presence = weakref.ref(new_lp)

class Presence(LocalPresenceObject):
    '''This represents a presence (self or someone else) that we've been told about, and information about it.'''

    def __init__(self, local_presence, name, info, old_me=None):
        '''Create a new presence info blob.

        Args:
            local_presence: The LocalPresence we belong to.
            name: The name of this presence.
            info: Dict of arbitrary information about the network (from e.g. a 'presence list' reply)
            old_me: Optional argument, if present - should be a Presence that we copy channels from.
        '''

        super(Presence, self).__init__(local_presence, name, info)

        if old_me is not None:
            self.channels = old_me.channels
        else:
            self.channels = set()

    def __repr__(self):
        return 'Presence(%r, %r, %r, <channels=%r>)' % (self.local_presence().connection, self.name, self.info, self.channels)

class Channel(LocalPresenceObject):
    '''This represents a channel that we've been told about, and information about it.'''

    def __init__(self, local_presence, name, info, old_me=None):
        '''Create a new channel info blob.

        Args:
            local_presence: The LocalPresence we belong to.
            name: The name of this channel.
            info: Dict of arbitrary information about the network (from e.g. a 'presence list' reply)
            old_me: Optional argument, if present - should be a Channel that we copy presences from.
        '''

        super(Channel, self).__init__(local_presence, name, info)

        if old_me is not None:
            self.presences = old_me.presences
        else:
            self.presences = {}

    def __repr__(self):
        return 'Channel(%r, %r, %r, <presences=%r>)' % (self.local_presence().connection, self.name, self.info, self.presences)
