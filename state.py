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

class StateObject(object):
    def __init__(self, params):
        self.__dict__.update(params)

class Network(StateObject):
    def __init__(self, params):
        super(Network, self).__init__(params)

class Gateway(StateObject):
    def __init__(self, params):
        super(Gateway, self).__init__(params)

class Presence(StateObject):
    def __init__(self, params):
        super(Presence, self).__init__(params)

class Channel(StateObject):
    def __init__(self, params):
        super(Channel, self).__init__(params)
