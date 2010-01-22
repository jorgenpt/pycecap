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

from state import Connection
from protocol import Reply

class StatefulMessage(object):
    '''Wrapper for icecap protocol messages (see protocol.py).
    
    This wraps a protocol Message of some kind and allows transparent access to it directly
    on this object (statefulmessage.params -> statefulmessage.message.params, etc).
    In addition, it adds the properties local_presence, connection, channel and presence that
    look up the referenced entity from the message in the current state (or returns None if
    the message doesn't refer to an entity of the kind).
    '''

    def __init__(self, state, message):
        self._state = weakref.ref(state)
        self._message = message

    def __getattr__(self, name):
        return getattr(self._message, name)

    @property
    def local_presence(self):
        if 'network' in self._message.params and 'mypresence' in self._message.params:
            return self._state().get_local_presence(self._message.params)
        elif isinstance(self._message, Reply):
            return self._message.command.local_presence
        else:
            return None

    @property
    def connection(self):
        if 'network' in self._message.params and 'mypresence' in self._message.params:
            return Connection(self._message.params['network'], self._message.params['mypresence'])
        elif isinstance(self._message, Reply):
            return self._message.command.connection
        else:
            return None

    @property
    def channel(self):
        local_presence = self.local_presence
        if local_presence and 'channel' in self._message.params:
            return local_presence.get_channel(self._message.params['channel'])
        elif isinstance(self._message, Reply):
            return self._message.command.channel
        else:
            return None

    @property
    def presence(self):
        local_presence = self.local_presence
        if local_presence and 'presence' in self._message.params:
            return local_presence.get_presence(self._message.params['presence'])
        elif isinstance(self._message, Reply):
            return self._message.command.presence
        else:
            return None

    @property
    def nonstate_params(self):
        state_keys = ['network', 'mypresence', 'channel', 'presence']
        return dict(((k, v) for k, v in self._message.params.iteritems() if not k in state_keys))
