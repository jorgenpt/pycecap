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
            'channel list': self.channel_list,
            'channel names': self.channel_presence_list,
        }

        self._state_handlers = {
            'network_init': self.network_add,
            'gateway_init': self.gateway_add,
            'presence_init': self.presence_add,
            'channel_init': self.channel_add,
            'channel_presence_init': self.channel_presence_add,
        }

        # Blank state.
        self._networks = {}

    def get(self, network_or_params, presence=None, channel=None):
        if isinstance(network_or_params, dict):
            network = network_or_params['network']
            presence = network_or_params.get('mypresence')
            channel = network_or_params.get('channel')
        else:
            network = network_or_params

        if network not in self._networks:
            self._networks[network] = state.Network()
        network = self._networks[network]

        if presence is None:
            return network

        if presence not in network.presences:
            network.presences[presence] = state.LocalPresence()
        presence = network.presences[presence]

        if channel is None:
            return presence

        if channel not in presence.channels:
            presence.channels[channel] = state.Channel()
        return presence.channels[channel]

    def presend(self, object_or_command, params=None):
        if isinstance(object_or_command, basestring):
            command = protocol.Command(str(self._next_tag), object_or_command, params)
        else:
            command = object_or_command
            command.tag = str(self._next_tag)

        self._next_tag += 1
        self._pending_commands[command.tag] = command

        return command

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
        new_networks = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                network = reply.params['network']
                new_networks[network] = state.Network(reply.params, self._networks.get(network))

        self._networks = new_networks

    def network_add(self, event):
        network = event.params['network']
        self._networks[network] = state.Network(event.params, self._networks.get(network))

    def gateway_list(self, command):
        for network in self._networks.iterkeys():
            self._networks[network].gateways = []

        for reply in command.replies:
            if reply.command == reply.MORE:
                gateway = reply.params
                self.get(gateway['network']).gateways.append(gateway)

    def gateway_add(self, event):
        gateway = event.params
        self.get(gateway['network']).gateways.append(gateway)

    def presence_list(self, command):
        for reply in command.replies:
            if reply.command == reply.MORE:
                network, presence = reply.params['network'], reply.params['mypresence']
                network = self.get(network)
                network.presences[presence] = state.LocalPresence(reply.params, network.presences.get(presence))

    def presence_add(self, event):
        if event.get('own'):
            network, presence = reply.params['network'], reply.params['presence']
            network = self.get(network)
            network.presences[presence] = state.LocalPresence(reply.params, network.presences.get(presence))

    def channel_list(self, command):
        presence = self.get(command.params)
        new_channels = {}

        for reply in command.replies:
            if reply.command == reply.MORE:
                channel = reply['channel']
                new_channels[channel] = state.Channel(reply.params, presence.channels.get(channel))

        presence.channels = new_channels

    def channel_add(self, event):
        network, presence, channel = event.params['network'], event.params['mypresence'], event.params['channel']
        presence = self.get(network, presence)

        presence.channels[channel] = state.Channel(event.params, presence.channels.get(channel))

    def channel_presence_list(self, command):
        channel = self.get(command.params)
        channel.presences = []
        for reply in command.replies:
            if reply.command == reply.MORE:
                channel.presences.append(reply.params)

    def channel_presence_add(self, event):
        channel = self.get(event.params)
        channel.presences.append(event.params)
