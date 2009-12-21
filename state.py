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

class Network(dict):
    def __init__(self, params={}, gateways=None):
        super(Network, self).__init__(params)

        if gateways is None:
            self.gateways = []
        else:
            self.gateways = gateways

    def __repr__(self):
        return 'Network(params=%s, gateways=%r)' % (super(Network, self).__repr__(), self.gateways)

class Channel(dict):
    def __init__(self, params={}, presences=None):
        super(Channel, self).__init__(params)

        if presences is None:
            self.presences = []
        else:
            self.presences = presences

    def __repr__(self):
        return 'Channel(params=%s, presences=%r)' % (super(Channel, self).__repr__(), self.presences)
