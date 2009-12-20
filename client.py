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

        # Default handlers to update self._{gateways,networks,presences,channels}.
        self._reply_handlers = {
            'network list': self.network_list,
            'gateway list': self.gateway_list,
            'presence list': self.presence_list,
            'channel list': self.channel_list
        }

        self._state_handlers = {
            'network_init': self.network_add,
            'gateway_init': self.gateway_add,
            'presence_init': self.presence_add,
            'channel_init': self.channel_add
        }

        # Blank state.
        self._networks = {}
        self._presences = []
        self._channels = []

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
        print "network_list(%r)" % command
        self._networks = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                network = reply.params['network']

                gateways = []
                if network in self._networks:
                    gateways = self._networks[network].gateways

                self._networks[network] = state.Network(reply.params, gateways)

    def network_add(self, event):
        print "network_add(%r)" % event
        network = event.params['network']

        gateways = []
        if network in self._networks:
            gateways = self._networks[network].gateways

        self._networks[network] = state.Network(event.params, gateways)

    def gateway_list(self, command):
        print "gateway_list(%r)" % command
        self._gateways = []
        for network in self._networks.iterkeys():
            self._networks[network][1] = []

        for reply in command.replies:
            if reply.command == reply.MORE:
                self._networks[gateway.network][1].append(gateway)

    def gateway_add(self, event):
        print "gateway_add(%r)" % event
        gateway = event.params
        if gateway['network'] not in self._networks:
            self._networks[gateway['network']] = state.Network()
        self._networks[gateway['network']].gateways.append(gateway)

    def presence_list(self, command):
        print "presence_list(%r)" % command
        self._presences = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._presences.append(reply.params)

    def presence_add(self, event):
        print "presence_add(%r)" % event
        self._presences.append(event.params)

    def channel_list(self, command):
        print "channel_list(%r)" % command
        self._channels = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                self._channels.append(reply.params)

    def channel_add(self, event):
        print "channel_add(%r)" % event
        self._channels.append(event.params)

