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

import state 

class StatefulMessage(object):
    '''Wrapper for icecap protocol messages (see protocol.py).
    
    This wraps a protocol Message of some kind and allows transparent access to it directly
    on this object (statefulmessage.params -> statefulmessage.message.params, etc).
    In addition, it adds the properties local_presence, connection, channel and presence that
    look up the referenced entity from the message in the current state (or returns None if
    the message doesn't refer to an entity of the kind).
    '''

    def __init__(self, state, message):
        self.state = weakref.ref(state)
        self.message = message

    def __getattr__(self, name):
        return getattr(self.message, name)

    def __setattr__(self, name, value):
        if name in ('state', 'message'): 
            return object.__setattr__(self, name, value)
        else:
            return setattr(self.message, name, value)

    @property
    def local_presence(self):
        if 'network' in self.message.params and 'mypresence' in self.message.params:
            return self.state().get_local_presence(self.message.params)
        else:
            return None

    @property
    def connection(self):
        if 'network' in self.message.params and 'mypresence' in self.message.params:
            return state.Connection(self.message.params['network'], self.message.params['mypresence'])
        else:
            return None

    @property
    def channel(self):
        local_presence = self.local_presence
        if local_presence and 'channel' in self.message.params:
            return local_presence.get_channel(self.message.params['channel'])
        else:
            return None

    @property
    def presence(self):
        local_presence = self.local_presence
        if local_presence and 'presence' in self.message.params:
            return local_presence.get_presence(self.message.params['presence'])
        else:
            return None
