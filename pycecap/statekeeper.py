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

class StateKeeper(object):
    '''A class to keep information about the current state.

    This is typically the class a client would inherit from (or instantiate)
    to keep a local state about what is known about the remote icecapd.
    '''

    def __init__(self):
        '''Create a new statekeeper.'''

        self.unhandled = (set(), set())
        self._next_tag = 1

        self._events = []
        self._pending_commands = {}

        # Default handlers to update self._{gateways,networks,presences,channels}.
        self._reply_handlers = {
            'network list': self._network_list,
            'gateway list': self._gateway_list,
            'presence list': self._local_presence_list,
            'channel list': self._channel_list,
            'channel names': self._channel_presence_list,
        }

        self._event_handlers = {
            'network_init': self._network_add,
            'gateway_init': self._gateway_add,
            'local_presence_init': self._local_presence_add,
            'local_presence_deinit': self._local_presence_remove,
            'presence_init': self._presence_add,
            'presence_deinit': self._presence_remove,
            'presence_changed': self._presence_changed,
            'channel_init': self._channel_add,
            'channel_deinit': self._channel_remove,
            'channel_presence_added': self._channel_presence_add,
            'channel_presence_removed': self._channel_presence_remove,
        }

        # Blank state.
        self.networks = {}
        self.local_presences = {}

    def presend(self, object_or_command, params=None):
        '''Notify the statekeeper that you're intending to send this.

        This causes the statekeeper to keep this command in it's "commands pending reply"
        queue, and also to update the command with a unique tag.

        Args:
            object_or_command: Either a command name or a Command instance.
            params: Only looked at if object_or_command is a command name - parameters
                to this command.

        Returns:
            A Command instance - either the one passed in with updated values, or a new
            one created from the passed values.
        '''

        if isinstance(object_or_command, basestring):
            command = protocol.Command(str(self._next_tag), object_or_command, params)
        else:
            command = object_or_command
            command.tag = str(self._next_tag)

        self._next_tag += 1
        self._pending_commands[command.tag] = command

        return command

    def parse(self, message):
        '''Parse a received message.

        This updates the internal state based on the received message.

        Args:
            message: A string (line) received from the server.
        '''

        if message.startswith('*'):
            event = protocol.Event(message)
            self._events.append(event)

            if event.command in self._event_handlers:
                self._event_handlers[event.command](event)
            else:
                self.unhandled[0].add(event.command)
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
                else:
                    self.unhandled[1].add(command.command)
                del self._pending_commands[reply.tag]

    def get_network(self, network):
        '''Get a Network instance for the given network name.

        This method creates a new Network and stores it with the given name if there
        is no Network with that name.
        '''

        if network not in self.networks:
            self.networks[network] = state.Network(network, {})
        return self.networks[network]

    def get_local_presence(self, connection):
        '''Get a LocalPresence for the given connection.

        This method creates a new LocalPresence and associates it with the given connection 
        if none is found.
        '''

        if not isinstance(connection, state.Connection):
            connection = state.Connection(connection)
        if connection not in self.local_presences:
            self.local_presences[connection] = state.LocalPresence(connection, {})
        return self.local_presences[connection]

    def _network_list(self, command):
        # Get a list of new networks from this reply,
        # retaining info from previous definitions (gateways)
        new_networks = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                network = reply.params.pop('network')
                new_networks[network] = state.Network(network, reply.params, self.networks.get(network))

        # Remove all local presences that refer to the no longer existing networks.
        old_networks = set(self.networks.iterkeys())
        removed_networks = old_networks - set(new_networks.iterkeys())
        for connection in self.local_presences.iterkeys():
            if connection.network in removed_networks:
                del self.local_presences[connection]

        # And instate new networks.
        self.networks = new_networks

    def _network_add(self, event):
        network = event.params.pop('network')
        # Add network - if network already exist, retain gateways associated with it.
        self.networks[network] = state.Network(network, event.params, self.networks.get(network))

    def _gateway_list(self, command):
        # Clear list of gateways for all networks, this is a "fresh start"
        for network in self.networks.iterkeys():
            self.networks[network].gateways = []

        for reply in command.replies:
            if reply.command == reply.MORE:
                network = reply.params.pop('network')
                # Add gateway to specified network, create network if needed.
                self.get_network(network).gateways.append(reply.params)

    def _gateway_add(self, event):
        network = event.params.pop('network')
        # Add gateway to specified network, create network if needed.
        self.get_network(network).gateways.append(event.params)

    def _local_presence_list(self, command):
        # Get a list of new presences
        new_presences = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                connection = state.Connection(reply.params)
                new_presences[connection] = state.LocalPresence(connection, reply.params, self.local_presences.get(connection))

        # Update all Channels and Users to refer to the right local_presence
        for local_presence in new_presences.itervalues():
            for channel in local_presence.channels:
                channel.reparent(self)
            for presence in local_presence.presences:
                presence.reparent(self)

        self.local_presences = new_presences

    def _local_presence_add(self, event):
        # Add a new local presence, overwriting any existing ones (retaining any channels & presences known by it)
        connection = state.Connection(event.params)
        self.local_presences[connection] = state.LocalPresence(connection, event.params, self.local_presences.get(connection))

    def _local_presence_remove(self, event):
        # Delete the given local presence, if it exists.
        connection = state.Connection(event.params)
        if connection in self.local_presences:
            del self.local_presences[connection]

    def _presence_add(self, event):
        # Add a new presence, overwriting any existing ones, but retaining any channel membership info.
        local_presence = self.get_local_presence(event.params)
        presence = event.params.pop('presence')

        local_presence.presences[presence] = state.Presence(local_presence, presence, event.params, local_presence.presences.get(presence))

    def _presence_remove(self, event):
        # Removes a presence, if it's there, and removes all channels that contain it.
        local_presence = self.get_local_presence(event.params)
        presence = event.params.pop('presence')

        presence_obj = local_presence.presences.pop(presence, None)

        if presence_obj is not None:
            for channel in presence_obj.channels:
                if channel in local_presence.channels:
                    local_presence.channels[channel].pop(presence, None)

    def _presence_changed(self, event):
        local_presence = self.get_local_presence(event.params)
        presence = event.params.pop('presence')
        presence_obj = local_presence.get_presence(presence)

        # The name param in presence_changed means the user changed nick / name,
        # and we need to update all references to the old name.
        if 'name' in event.params:
            new_presence = event.params.pop('name')
            local_presence.presences[new_presence] = presence_obj

            # For every channel the presence was in, update the references in the channel object.
            for channel in presence_obj.channels:
                channel_obj = local_presence.channels.get(channel)
                if channel_obj:
                    old_mode = channel_obj.presences.pop(presence, '')
                    channel_obj.presences[new_presence] = old_mode

            # Then finally, delete the old entry.
            del local_presence.presences[presence]
            presence = new_presence

        # Otherwise, these are attributes where we just update the info-dict for the presence.
        INFO_KEYS = ['address'] # TODO: More keys?
        for key in INFO_KEYS:
            if key in event.params:
                new_info = event.params.pop(key)
                presence_obj.info[key] = new_info

    def _channel_list(self, command):
        # Build a dict of Connection-to-<name-to-Channel> from this reply.
        new_channels = {}
        for reply in command.replies:
            if reply.command == reply.MORE:
                connection = state.Connection(reply.params)
                local_presence = self.get_local_presence(connection)
                if connection not in new_channels:
                    new_channels[connection] = {}

                channel = reply.params.pop('channel')
                new_channels[connection][channel] = state.Channel(local_presence, channel, reply.params, local_presence.channels.get(channel))

        # Go over every Connection, if it's in the new list, update it, otherwise clear it.
        for (connection, presence) in self.local_presences.iteritems():
            if connection in new_channels:
                presence.channels = new_channels[connection]
            else:
                presence.channels = {}

    def _channel_add(self, event):
        # Add a channel, retain any presences in it if it already exists.
        local_presence = self.get_local_presence(event.params)
        channel = event.params.pop('channel')
        local_presence.channels[channel] = state.Channel(local_presence, channel, event.params, local_presence.channels.get(channel))

    def _channel_remove(self, event):
        # Remove a channel, if it exists, and remove any presences presnece listed as being in it
        local_presence = self.get_local_presence(event.params)
        channel = event.params.pop('channel')

        channel_obj = local_presence.channels.pop(channel, None)

        if channel_obj is not None:
            for presence in channel_obj.presences.iterkeys():
                if presence in local_presence.presences:
                    local_presence.presences[presence].channels.pop(channel, None)

    def _channel_presence_list(self, command):
        # Replace the presencelist for a channel with these new ones.
        local_presence = self.get_local_presence(command.params)
        channel = local_presence.get_channel(command.params.pop('channel'))

        old_presences = set(channel.presences.iterkeys())
        channel.presences = {}


        for reply in command.replies:
            if reply.command == reply.MORE:
                presence = reply.params.pop('presence')
                mode = reply.params.pop('mode', '')
                channel.presences[presence] = mode
                local_presence.get_presence(presence).channels.add(channel)

        # Remove channel from channel-list of presences which weren't present in the new list.
        removed_presences = old_presences - set(channel.presences.iterkeys())
        for presence in removed_presences:
            local_presence.get_presence(presence).channels.discard(channel)

    def _channel_presence_add(self, event):
        # Link a presence to a channel
        local_presence = self.get_local_presence(event.params)
        channel = event.params.pop('channel')
        presence = event.params.pop('presence')

        local_presence.get_channel(channel).presences[presence] = ''
        local_presence.get_presence(presence).channels.add(channel)

    def _channel_presence_remove(self, event):
        # Remove a link between a presence and a channel
        local_presence = self.get_local_presence(event.params)
        channel = event.params.pop('channel')
        presence = event.params.pop('presence')

        local_presence.get_channel(channel).presences.pop(presence, None)
        local_presence.get_presence(presence).channels.discard(channel)
