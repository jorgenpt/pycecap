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

import protocol
import state

import sys


class Client(object):
    def __init__(self):
        self._next_tag = 1

        self._events = []
        self._pending_commands = {}
        self._event_handlers = {}
        self._state_handlers = {}

        # Default handlers to update self._{gateways,networks,presences,channels}.
        self._reply_handlers = {
            'network list': self.network_list,
            'gateway list': self.gateway_list,
            'presence list': self.presence_list,
            'channel list': self.channel_list
        }

        # No state until we get the first "foo list" replies.
        self._gateways = {}
        self._networks = {}
        self._presences = {}
        self._channels = {}

    def presend(self, object_or_command, params=None):
        if isinstance(object_or_command, basestr):
            command = protocol.Command(str(self._next_tag), object_or_command, params)
        else:
            command = object_or_command
            command.tag = self._next_tag

        self._next_tag += 1
        self._pending_commands[command.tag] = command

        return command

    def fakesend(self, command):
        command = protocol.Command(command)
        self._pending_commands[command.tag] = command

    def parse(self, message):
        if message.startswith('*'):
            event = protocol.Event(message)
            self._events.append(event)

            if event.command in self._state_handlers:
                self._state_handlers[event.command](event)

            if event.command in self._event_handlers:
                self._event_handlers[event.command](event)
        else:
            reply = protocol.Reply(message)

            if not reply.tag in self._pending_commands:
                print >>sys.stderr, "Got reply for non-pending tag '%s'" % reply.tag
                return

            command = self._pending_commands[reply.tag]
            command.received_reply(reply)

            if reply.command == reply.OK:
                if command.command in self._reply_handlers:
                    self._reply_handlers[command.command](command)
                del self._pending_commands[reply.tag]

    def network_list(self, command):
        self._networks = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._networks[reply.params['network']] = state.Network(reply.params)

    def gateway_list(self, command):
        self._gateways = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._gateways.append(state.Gateway(reply.params))

    def presence_list(self, command):
        self._presences = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._presences.append(state.Presence(reply.params))

    def channel_list(self, command):
        self._channels = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._channels.append(state.Channel(reply.params))
