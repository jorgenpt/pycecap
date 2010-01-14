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

'''A set of classes and functions to parse & generate icecap messages.'''

class InvalidMessageException(Exception):
    '''Attempted to parse an icecap message that was not understood.'''

ESCAPE_LOOKUP = {'.': ';', 'r': "\r", 'n': "\n"}

def unescape(s):
    '''Unescape a icecap protocol message part.

    Icecap escapes ';' as '\\.', and '\\' as '\\\\'. This gets the original string
    back, typically used after splitting a protocol message into its separate
    parts.'''

    unesc = ''

    escape = False
    for c in str(s):
        if escape:
            c = ESCAPE_LOOKUP.get(c, c)
        else:
            escape = (c == '\\')
            if escape:
                c = ''

        unesc += c

    return unesc

def escape(s):
    '''Escape a icecap protocol message part.

    Icecap requires ';' to be escaped as '\\.', and since the protocol is line-
    based, CR & LF are also escaped. For a literal '\\', it's replaced with '\\\\'.
    '''
    return str(s).replace('\\', '\\\\').replace(';', '\\.').replace('\n', '\\n').replace('\r', '\\r')

class Message(object):
    '''Represent an icecap protocol message (any type).

    These are general parts that *all* icecap messages have. Look at Command, Reply 
    and Event for specifics of those messages.
    '''
    def __init__(self):
        '''Create a new, empty message.'''
        self.message = None
        self.command = ''
        self.tag = ''
        self.params = {}

    def parse(self, message):
        '''Populate this message with data from the given string.'''
        parts = message.split(';')
        if len(parts) < 2:
            raise InvalidMessageException('Not at least two parts in the message.')

        params = filter(len, parts[2:])

        self.message = message
        self.tag, self.command = parts[:2]
        self.params = {}

        for param in params:
            parts = param.split('=', 1)
            key = parts[0]

            if len(parts) > 1:
                self.params[key] = unescape(parts[1])
            else:
                self.params[key] = True

    def __str__(self):
        '''Get a protocol-compliant textual representation of this message.'''
        params = []
        for (k, v) in self.params.iteritems():
            if v is True:
                params.append(escape(k))
            else:
                params.append('%s=%s' % (escape(k), escape(v)))
        return '%s;%s;%s' % (escape(self.tag), escape(self.command), ';'.join(params))

    def __repr__(self):
        className = self.__class__.__name__
        if not self.command:
            return '%s(message=%r)' % (className, self.message)
        else:
            return '%s(command=%r, tag=%r, params=%r)' % (className, self.command, self.tag, self.params)

class Command(Message):
    '''Represent a command, sent from the client to the server.

    http://icecap.irssi2.org/IcecapProtocol/Introduction#Commands
    '''

    def __init__(self, message_or_tag, command=None, params=None):
        '''Create a new Command from the given data.

        Args:
            message_or_tag: Either a string (from the network) we parse or the tag of the new message.
            command: Defaults to None, which means we treat message_or_tag as a message, otherwise
                a tag. Defines the name of the command we're sending.
            params: A dict of parameters or None if no params / parse from message.
        '''
        super(Command, self).__init__()

        self.replies = []

        if command is None:
            self.parse(message_or_tag)
        else:
            self.tag = message_or_tag
            self.params = params or {}
            self.command = command

    def received_reply(self, reply):
        '''Register a reply received for this specific command.'''
        self.replies.append(reply)

class Reply(Message):
    '''Represent a reply to a command, sent from the server to the client.

    http://icecap.irssi2.org/IcecapProtocol/Introduction#Command_replies
    '''

    OK = 0
    FAIL = 1
    MORE = 2

    STATUS = {
        '+': OK,
        '-': FAIL,
        '>': MORE
    }
    STATUS_REVERSE = dict(((v, k) for k, v in STATUS.iteritems()))

    def __init__(self, message_or_tag, status=None, params=None):
        '''Create a new Reply from the given data.

        Args:
            message_or_tag: Either a string (from the network) we parse or the tag the reply corresponds to.
            status: Defaults to None, which means we treat message_or_tag as a message, otherwise
                a tag. Defines the status code of the reply (see Reply.STATUS's values for valid ones).
            params: A dict of parameters or None if no params / parse from message.
        '''
        super(Reply, self).__init__()

        if status is None:
            self.parse(message_or_tag)
            if not self.command in self.STATUS:
                raise InvalidMessageException("Reply status '%s' is not known" % self.command)
            self.command = self.STATUS[self.command]
        else:
            if not status in self.STATUS_REVERSE:
                raise InvalidMessageException("Reply status %i is not known" % status)

            self.tag = message_or_tag
            self.params = params or {}
            self.command = self.STATUS_REVERSE[status]

class Event(Message):
    '''Represent an event that occurs, sent from the server to the client.

    http://icecap.irssi2.org/IcecapProtocol/Introduction#Command_replies
    '''

    def __init__(self, message_or_name, params=None):
        '''Create a new Event from the given data.

        Args:
            message_or_name: Either a string (from the network) we parse or the name of the event.
            params: A dict of parameters or None if message_or_name is a message.
        '''
        super(Event, self).__init__()

        if params is None:
            self.parse(message_or_name)
        else:
            self.tag = None
            self.command = message_or_name
            self.params = params
