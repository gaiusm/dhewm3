#!/usr/bin/env python

# Copyright (C) 2017
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
# Author Gaius Mulley <gaius@gnu.org>
#

import time
import socket
import sys
import os

from botaa import aas
from botbasic import basic
from botcache import cache
from chvec import *
from math import atan2

pen2doom3units = 48   # inches per ascii square


class bot:
    #
    #  __init__ the constructor for bot class which
    #           joins together all the lower layers in the AI
    #

    def __init__ (self, server, name):
        self._cache = cache (server, name)
        self._aas = aas (self.getPenMapName ())
        initPosPen = self._aas.getPlayerStart ()
        initPosD3 = self._cache.getPlayerStart ()
        self._scaleX = float (pen2doom3units)
        self._scaleY = float (pen2doom3units)
        print "initPosPen =", initPosPen, "initPosD3 =", initPosD3


    #
    #  getPenMapName - return the name of the pen map.
    #

    def getPenMapName (self):
        return self._cache.getPenMapName ()


    #
    #  me - return the bots entity, id.
    #

    def me (self):
        return self._cache.me ()


    #
    #  maxobj - return the maximum number of registered, ids in the game.
    #           Each monster, player, ammo pickup has an id
    #

    def maxobj (self):
        return self._cache.maxobj ()


    #
    #  allobj - return a list of all objects
    #

    def allobj (self):
        return self._cache.allobj ()


    #
    #  getpos - return the position of, obj in doom3 units.
    #

    def getpos (self, obj):
        return self._cache.getpos (obj)

    #
    #  forward - step forward at velocity, vel, for dist, units.
    #

    def forward (self, vel, dist):
        return self._cache.forward (vel, dist)

    #
    #  back - step back at velocity, vel, for dist, units.
    #

    def back (self, vel, dist):
        return self._cache.back (vel, dist)

    #
    #  left - step left at velocity, vel, for dist, units.
    #

    def left (self, vel, dist):
        return self._cache.left (vel, dist)

    #
    #  right - step right at velocity, vel, for dist, units.
    #

    def right (self, vel, dist):
        return self._cache.right (vel, dist)

    #
    #  turn - turn to face, angle.
    #

    def turn (self, angle, angle_vel):
        return self._cache.turn (angle, angle_vel)

    #
    #  select - wait for any desired event:  legal events are
    #           ['move', 'fire', 'turn', 'reload'].
    #

    def select (self, l):
        return self._cache.select (l)

    #
    #  sync - wait for any event to occur.
    #         The event will signify the end of
    #         move, fire, turn, reload action.
    #

    def sync (self):
        return self._cache.sync ()

    #
    #  angle - return the angle the object, d, is facing.
    #          d is only sensibly used with monsters and players.
    #  (not implemented yet)
    #

    def angle (self, d):
        return 0

    #
    #  calcnav - calculate the navigation route between us and object, d.
    #            No movement is done, it only works out the best route.
    #            This is quite expensive and should be used sparingly.
    #            It returns the total distance between ourself and
    #            object, d, assuming this route was followed.  Notice
    #            this is not the same as a line of sight distance.
    #            The distance returned is a doom3 unit.
    #

    def calcnav (self, d):
        src = self.d2pv (self.getpos (self.me ()))
        dest = self.d2pv (self.getpos (d))
        return self.p2d (self._aas.calcnav (src, dest))


    #
    #  turnface - turn and face vector.
    #

    def turnface (self, v, vel):
        print "v =", v,
        if v[0] == 0:
            print "not using atan2"
            if v[1] > 0:
                angle = 180
            else:
                angle = 0
        elif v[1] == 0:
            print "not using atan2"
            if v[0] > 0:
                angle = 90
            else:
                angle = 270
        else:
            print "using atan2"
            angle = int (atan2 (v[0], v[1]) * 180.0)   # radians into degrees
            angle += 360
            angle %= 360
        print "angle =", angle
        self.turn (angle, vel)


    #
    #  d2pv - convert a doom3 coordinate into a penguin tower coordinate.
    #         converted vector is returned.
    #

    def d2pv (self, v):
        r = []
        if len (v) > 1:
            r += [v[1]/(-pen2doom3units)+1]   # x and y are switched between maps
            r += [v[0]/(-pen2doom3units)+1]
        return r

    #
    #  p2d - in:   a penguin tower unit.
    #        out:  return a d3 unit.
    #

    def p2d (self, u):
        return pen2doom3units * u

    #
    #  journey - move at velocity, vel, for a distance, dist
    #            along the navigation route calculated in calcnav.
    #

    def journey (self, vel, dist, dest):
        dest = self.d2pv (dest)
        print "aas.getHop (0) =", self._aas.getHop (0), "my pos =", self.d2pv (self.getpos (self.me ()))
        while (dist > 0) and (vel != 0) and (not equVec (self._aas.getHop (0), dest)):
            dist = self.ssNav (vel, dist, self._aas.getHop (0))
            print "journey: reached coord", self._aas.getHop (0)
            self._aas.removeHop (0, self.d2pv (self.getpos (self.me ())))
        self.reset ()


    #
    #  ssNav - single square navigate, turn and move to position, h,
    #          which should be an adjacent square.
    #

    def ssNav (self, vel, dist, h):
        p = self.d2pv (self.getpos (self.me ()))
        while (dist > 0) and (not equVec (h, p)):
            self.turnface (subVec (h, p), vel)
            self.sync ()
            if dist > self.p2d (1):
                d = self.p2d (1)
            else:
                d = dist
            self.forward (vel, d)
            self.sync ()
            dist -= d
            p = self.d2pv (self.getpos (self.me ()))
        return dist


    #
    #  face - turn to face object, i.  If we are close we attempt to aim
    #         at object.
    #

    def face (self, i):
        self.reset ()
        p = self.d2pv (self.getpos (self.me ()))
        h = self.d2pv (self.getpos (i))
        self.turnface (subVec (h, p), 1)
        self.sync ()
        if equVec (p, h):
            self.aim (i)


    #
    #  aim - aim at object, i.
    #

    def aim (self, i):
        self._cache.reset ()
        self._cache.aim (i)

    #
    #  reset - reset the cache.
    #

    def reset (self):
        self._cache.reset ()
