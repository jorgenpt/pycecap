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

class InvalidMessageException(Exception):
    pass

ESCAPE_LOOKUP = {'.': ';', 'r': "\r", 'n': "\n"}

def unescape(s):
    unesc = ''

    escape = False
    for c in str(s):
        if escape:
            c = self.ESCAPE_LOOKUP.get(c, c)
        else:
            escape = (c == '\\')
            if escape:
                c = ''

        unesc += c

    return unesc

def escape(s):
    return str(s).replace('\\', '\\\\').replace(';', '\\.').replace('\n', '\\n').replace('\r', '\\r')

class Message(object):
    def __init__(self):
        self.message = None
        self.command = ''
        self.tag = ''
        self.params = {}

    def parse(self, message):
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
    def __init__(self, message_or_tag, command=None, params=None):
        super(Command, self).__init__()

        self.replies = []

        if command is None:
            self.parse(message_or_tag)
        else:
            self.tag = message_or_tag
            self.params = params or {}
            self.command = command

    def received_reply(self, reply):
        self.replies.append(reply)

class Reply(Message):
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
    def __init__(self, message_or_name, params=None):
        super(Event, self).__init__()

        if params is None:
            self.parse(message_or_name)
        else:
            self.tag = None
            self.command = message_or_name
            self.params = params
