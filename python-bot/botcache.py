#!/usr/bin/env python3

# Copyright (C) 2017-2019
#               Free Software Foundation, Inc.
# This file is part of Chisel
#
# Chisel is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# Chisel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chisel; see the file COPYING.  If not, write to the
# Free Software Foundation, 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Author Gaius Mulley <gaius.mulley@southwales.ac.uk>
#

import time
import socket
import sys
import os

from botbasic import basic


#
#  the purpose of the cache class is to replicate the functionality
#  in the basic class, but it attempts to look a value before using
#  a remote procedure call.
#
#  A number of these methods are not cached, but they are implemented
#  in the cache class so that the basic class can be completely hidden
#  from the higher level code.
#

class cache:
    #
    #  __init__ the cache constructor.
    #

    def __init__ (self, server, name):
        self._basic = basic (server, name)
        self._dict = {}

    #
    #  reset - delete all the cached values.
    #

    def reset (self):
        print("reset cache")
        self._dict = {}

    #
    #  getPenName - return the name of the pen map.
    #

    def getPenName (self):
        if 'getpenname' not in self._dict:
            self._dict['getpenname'] = self._basic.genPenName ()
        return self._dict['getpenname']

    #
    #  getpos - return the position of, obj in doom3 units.
    #

    def getpos (self, obj):
        l = 'getpos_%d' % (obj)
        if l not in self._dict:
            self._dict[l] = self._basic.getpos (obj)
        return self._dict[l]

    #
    #  me - return the bots entity, id.
    #

    def me (self):
        if 'me' not in self._dict:
            self._dict['me'] = self._basic.me ()
        return self._dict['me']

    #
    #  maxobj - return the maximum number of registered, ids in the game.
    #           Each monster, player, ammo pickup has an id
    #

    def maxobj (self):
        if 'maxobj' not in self._dict:
            self._dict['maxobj'] = self._basic.maxobj ()
        return self._dict['maxobj']

    #
    #  allobj - return a list of all objects
    #

    def allobj (self):
        return list(range(1, self.maxobj () + 1))

    #
    #  objectname - return the name of the object, d.
    #

    def objectname (self, d):
        l = "objectname %d\n" % (d)
        if l not in self._dict:
            self._dict[l] = self._basic.objectname (d)
        return self._dict[l]

    #
    #  isvisible - return True if object, d, is line of sight visible.
    #

    def isvisible (self, d):
        l = "isvisible %d\n" % (d)
        if l not in self._dict:
            self._dict[l] = self._basic.isvisible (d)
        return self._dict[l]

    #
    #  isfixed - return True if the object is a static fixture in the map.
    #

    def isfixed (self, d):
        l = "isfixed %d\n" % (d)
        if l not in self._dict:
            self._dict[l] = self._basic.isvisible (d)
        return self._dict[l]


    #
    #  right - step right at velocity, vel, for dist, units.
    #

    def right (self, vel, dist):
        self.delpos (self.me ())
        return self._basic.right (vel, dist)

    #
    #  forward - step forward at velocity, vel, for dist, units.
    #

    def forward (self, vel, dist):
        self.delpos (self.me ())
        return self._basic.forward (vel, dist)

    #
    #  left - step left at velocity, vel, for dist, units.
    #

    def left (self, vel, dist):
        return self.right (-vel, dist)

    #
    #  back - step back at velocity, vel, for dist, units.
    #

    def back (self, vel, dist):
        return self.forward (-vel, dist)

    #
    #  stepvec - step forward at velocity, velforward and velright for
    #            dist, units.
    #

    def stepvec (self, velforward, velright, dist):
        self.delpos (self.me ())
        return self._basic.stepvec (velforward, velright, dist)

    #
    #  sync - wait for any event to occur.
    #         The event will signify the end of
    #         move, fire, turn, reload action.
    #

    def sync (self):
        self.delpos (self.me ())
        return self._basic.sync ()

    #
    #  select - wait for any event:  legal events are
    #           ['move', 'fire', 'turn', 'reload'].
    #

    def select (self, l):
        return self._basic.select (l)
        self.delpos (self.me ())

    #
    #  start_firing - fire weapon
    #                 It returns the amount of ammo left.
    #

    def start_firing (self):
        self.delammo ()
        return self._basic.start_firing ()

    #
    #  stop_firing - stop firing weapon
    #                It returns the amount of ammo left.
    #

    def stop_firing (self):
        self.delammo ()
        return self._basic.stop_firing ()

    #
    #  reload_weapon - reload the current weapon
    #                  It returns the amount of ammo left.
    #

    def reload_weapon (self):
        return self._basic.reload_weapon ()

    #
    #  ammo - returns the amount of ammo for the current weapon.
    #

    def ammo (self):
        if 'ammo' not in self._dict:
            self._dict['ammo'] = self._basic.ammo ()
        return self._dict['ammo']

    #
    #  aim - aim weapon at player, i
    #

    def aim (self, i):
        print("cache aim")
        return self._basic.aim (i)

    #
    #  angle - return the angle the bot is facing.
    #          The angle returned is a penguin tower angle.
    #          0 up, 180 down, 90 left, 270 right.
    #          Equivalent to the doom3 Yaw.
    #

    def angle (self):
        if 'angle' not in self._dict:
            self._dict['angle'] = self._basic.angle ()
        return self._dict['angle']

    #
    #  turn - turn to face, angle.
    #

    def turn (self, angle, angle_vel):
        self.delpos (self.me ())
        return self._basic.turn (angle, angle_vel)

    #
    #  delpos - deletes the cached entry for position of object, i.
    #

    def delpos (self, i):
        l = 'getpos_%d' % (i)
        self._dict.pop (l, None)

    #
    #  delammo - deletes the cached entry of ammo.
    #

    def delammo (self):
        self._dict.pop ('ammo', None)


    #
    #  getPenMapName - return the name of the current pen map.
    #

    def getPenMapName (self):
        if 'getpenmapname' not in self._dict:
            self._dict['getpenmapname'] = self._basic.getPenMapName ()
        return self._dict['getpenmapname']

    #
    #  getTag - returns the tag value in the map file.
    #
    
    def getTag (self, name):
        tagname = "tag " + name
        if tagname not in self._dict:
            self._dict[tagname] = self._basic.getTag (name)
        return self._dict[tagname]

    #
    #  getPlayerStart - return the player start location.
    #

    def getPlayerStart (self):
        if 'info_player_start' not in self._dict:
            self._dict['info_player_start'] = self._basic.getPlayerStart ()
        return self._dict['info_player_start']


    #
    #  getEntityNo - return the entity number which contains the
    #                pair of strings left, right.
    #

    def getEntityNo (self, left, right):
        name = "entitynamed %s %s" % (left, right)
        if name not in self._dict:
            self._dict[name] = self._basic.getEntityNo (left, right)
        return self._dict[name]


    #
    #  getEntityPos - return the spawn position of entity_no in the static doom3 map.
    #                 The return result is a doom3 [x, y, z] coordinate.
    #

    def getEntityPos (self, entity_no):
        name = "entity %d" % entity_no
        if name not in self._dict:
            self._dict[name] = self._basic.getEntityPos (entity_no)
        return self._dict[name]

    #
    #  getSpawnPos - return the doom3 [x, y, z] of this bots spawn location.
    #

    def getSpawnPos (self):
        return self.getEntityPos (self.me ())

    #
    #  getEntityName - returns the name string for, entity_no.
    #

    def getEntityName (self, entity_no):
        name = "entity name %d" % entity_no
        if name not in self._dict:
            self._dict[name] = self._basic.getEntityName (entity_no)
        return self._dict[name]
