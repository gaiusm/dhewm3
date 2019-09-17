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
import random

from botaa import aas
from botbasic import basic
from botcache import cache
from chvec import *
from math import atan2, sqrt

debugging = False

pen2doom3units = 48   # inches per ascii square
angle_offset = 0

#
#  sqr - return the square of x.
#

def sqr (x):
    return x * x


#
#  incAngle - increments, angle, by, inc, ensuring it stays within 0..359 degrees.
#

def incAngle (angle, inc):
    angle += inc
    while angle < 0:
        angle += 360
    angle %= 360
    return angle


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
        if debugging:
            print("initPosPen =", initPosPen, "initPosD3 =", initPosD3)


    #
    #  getPenMapName - return the name of the pen map.
    #

    def getPenMapName (self):
        return self._cache.getPenMapName ()


    #
    #  me - return the bots entity, id.
    #

    def me (self):
        self._aas.printFloor ()
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
        p = self._cache.getpos (obj)
        return [p[0], p[1], p[2]]

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
    #  atod3 - convert a penguin tower map angle into the doom3 angle.
    #

    def atod3 (self, angle):
        return incAngle (angle, angle_offset)

    #
    #  turn - turn to face, angle.  The angle is a penguin tower angle.
    #         0 up, 180 down, 90 left, 270 right.
    #

    def turn (self, angle, angle_vel):
        return self._cache.turn (self.atod3 (angle), angle_vel)

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
    #  angle - return the angle the bot is facing.
    #          The angle returned is a penguin tower angle.
    #          0 up, 180 down, 90 left, 270 right.
    #          Equivalent to the doom3 Yaw.
    #

    def angle (self):
        return self._cache.angle ()

    #
    #  calcnav - calculate the navigation route between us and object, d.
    #            No movement is done, it only works out the best route.
    #            This is quite expensive and should be used sparingly.
    #            It returns the total distance between ourself and
    #            object, d, assuming this route was followed.  Notice
    #            this is not the same as a line of sight distance.
    #            The distance returned is in penguin tower units.
    #

    def calcnav (self, d):
        self.reset ()
        src = self.d2pv (self.getpos (self.me ()))
        dest = self.d2pv (self.getpos (d))
        return self._aas.calcnav (src, dest)


    #
    #  calcnav_pos - calculate the navigation route between us and position, dest.
    #                No movement is done, it only works out the best route.
    #                This is quite expensive and should be used sparingly.
    #                It returns the total distance between ourself and
    #                dest, assuming this route was followed.  Notice
    #                this is not the same as a line of sight distance.
    #                The distance returned is in penguin tower units.
    #

    def calcnav_pos (self, dest):
        self.reset ()
        src = self.d2pv (self.getpos (self.me ()))
        return self._aas.calcnav (src, dest)


    #
    #  calcAngle - calculate the angle to face vector, v.
    #

    def _calcAngle (self, v):
        if v[0] == 0:
            if debugging:
                print("short cut, not using atan2 north/south", end=' ')
            if v[1] > 0:
                angle = 270
            else:
                angle = 90
        elif v[1] == 0:
            if debugging:
                print("short cut, not using atan2 left/right", end=' ')
            if v[0] > 0:
                angle = 180
            else:
                angle = 0
        else:
            if debugging:
                print("using atan2", end=' ')
            angle = incAngle (int (atan2 (v[1], v[0]) * 180.0 / 3.1415927), 180)   # radians into degrees

        if debugging:
            print("angle =", angle)
        return angle

    #
    #  turnface - turn and face vector.
    #

    def turnface (self, v, vel = None):
        if debugging:
            print("v =", v, end=' ')
        angle = self._calcAngle (v)
        if vel == None:
            #
            #  we work out the quickest anti/clock turn to achieve correct orientation.
            #
            old = self.angle ()
            if old < angle:
                if abs (old + 360 - angle) < abs (angle - old):
                    self.turn (angle, -1)  # quicker to turn using -1
                else:
                    self.turn (angle, 1)  # quicker to turn using 1
            else:
                if abs (angle + 360 - old) < abs (angle - old):
                    self.turn (angle, 1)  # quicker to turn using 1
                else:
                    self.turn (angle, -1)  # quicker to turn using -1
        else:
            self.turn (angle, vel)


    #
    #  d2pv - convert a doom3 coordinate into a penguin tower coordinate.
    #         converted vector is returned.
    #

    def d2pv (self, v):
        r = []
        if len (v) > 1:
            r += [int (v[0]/(-pen2doom3units)) + 1]
            r += [int (v[1]/(-pen2doom3units))]
        print ("doom units, v =", v, "pen coord =", r)
        return r

    #
    #  p2d - in:   a penguin tower unit.
    #        out:  return a d3 unit.
    #

    def p2d (self, u):
        if u is None:
            return None
        return pen2doom3units * u

    #
    #  journey - move at velocity, vel, for a distance, dist
    #            along the navigation route calculated in calcnav.
    #            dist is in penguin tower units.  This function
    #            will return early if the object moves position.
    #

    def journey (self, vel, dist, obj):
        self.reset ()
        if debugging:
            print ("journey along route", self._aas._route)
        dest = self.d2pv (self.getpos (obj))
        dist = self.p2d (dist) # convert to doom3 unit
        if debugging:
            print ("aas.getHop (0) =", self._aas.getHop (0), "my pos =", self.d2pv (self.getpos (self.me ())), "dest =", dest)
        print ("aas.getHop (0) =", self._aas.getHop (0), "my pos =", self.d2pv (self.getpos (self.me ())), "dest =", dest)
        #
        #  keep stepping along route as long as the object does not move and we have dist units to move along
        #
        while (dist > 0) and (vel != 0) and equVec (dest, self.d2pv (self.getpos (obj))) and (not equVec (self._aas.getHop (0), dest)):
            v = subVec (self.d2pv (self.getpos (self.me ())), self._aas.getHop (0))
            hopPos = self._aas.getHop (0)
            hops = 1
            while (hops < self._aas.noOfHops ()) and equVec (subVec (hopPos, self._aas.getHop (hops)), v):
                hopPos = self._aas.getHop (hops)
                hops += 1
            if hops == 1:
                if debugging:
                    print("single hop nav")
                dist = self.ssNav (vel, dist, self._aas.getHop (0))
                if debugging:
                    print("old journey route", self._aas._route)
                    print("journey: reached coord", self._aas.getHop (0))
                self._aas.removeHop (0, self.d2pv (self.getpos (self.me ())))
                if debugging:
                    print("new journey route", self._aas._route)
            else:
                if debugging:
                    print("bulk hop nav", hops)
                dist = self.ssBulkNav (vel, self._aas.getHop (hops-1), hops)
                if dist > 0:
                    self.reset ()
                    mypos = self.d2pv (self.getpos (self.me ()))
                    for h in range (hops):
                        if equVec (mypos, self._aas.getHop (h)):
                            for i in range (h):
                                self._aas.removeHop (0, self._aas.getHop (0))
                            break
                    else:
                        if debugging:
                            print("oops fallen off the route, aborting and will try again")
                        return
                    hops = 0
                    if debugging:
                        print("new journey route", self._aas._route)
        if debugging:
            if dist == 0:
                print("journey algorithm ran out of distance")
            elif equVec (dest, self.d2pv (self.getpos (obj))):
                print("journey algorithm reached the goal object")
            elif equVec (self._aas.getHop (0), dest):
                print("journey algorithm reached intemediate hop")
            else:
                print("journey algorithm failed")
        self.reset ()



    #
    #  journey_pos - move at velocity, vel, for a distance, dist
    #                along the navigation route calculated in calcnav
    #                to dest.  dist is in penguin tower units.
    #                dest is a penguin tower coordinate.
    #

    def journey_pos (self, vel, dist, dest):
        self.reset ()
        if debugging:
            print("journey along route", self._aas._route)
        dist = self.p2d (dist) # convert to doom3 unit
        if debugging:
            print("aas.getHop (0) =", self._aas.getHop (0), "my pos =", self.d2pv (self.getpos (self.me ())), "dest =", dest)
        #
        #  keep stepping along route as long as we have dist units remaining
        #
        while (dist > 0) and (vel != 0) and (not equVec (self._aas.getHop (0), dest)):
            v = subVec (self.d2pv (self.getpos (self.me ())), self._aas.getHop (0))
            hopPos = self._aas.getHop (0)
            hops = 1
            while (hops < self._aas.noOfHops ()) and equVec (subVec (hopPos, self._aas.getHop (hops)), v):
                hopPos = self._aas.getHop (hops)
                hops += 1
            if hops == 1:
                if debugging:
                    print("single hop nav")
                dist = self.ssNav (vel, dist, self._aas.getHop (0))
                if debugging:
                    print("old journey route", self._aas._route)
                    print("journey: reached coord", self._aas.getHop (0))
                self._aas.removeHop (0, self.d2pv (self.getpos (self.me ())))
                if debugging:
                    print("new journey route", self._aas._route)
            else:
                if debugging:
                    print("bulk hop nav", hops)
                dist = self.ssBulkNav (vel, self._aas.getHop (hops-1), hops)
                if dist > 0:
                    self.reset ()
                    mypos = self.d2pv (self.getpos (self.me ()))
                    for h in range (hops):
                        if equVec (mypos, self._aas.getHop (h)):
                            for i in range (h):
                                self._aas.removeHop (0, self._aas.getHop (0))
                            break
                    else:
                        if debugging:
                            print("oops fallen off the route, aborting and will try again")
                        return
                    hops = 0
                    if debugging:
                        print("new journey route", self._aas._route)
        if debugging:
            if dist == 0:
                print("journey algorithm ran out of distance")
            elif equVec (self._aas.getHop (0), dest):
                print("journey algorithm reached intemediate hop")
            else:
                print("journey algorithm failed")
        self.reset ()


    def calcMidDist (dest):
        botpos = self.getpos (self.me ())  # doom3 units


    def runArc (self, angle, dist):
        self.forward (100, dist)
        self.turn (angle, 1)
        self.select (["move"])
        self.select (["turn"])


    def midPen2Doom (self, p):
        return [p[0] * pen2doom3units + pen2doom3units/2,
                p[1] * pen2doom3units + pen2doom3units/2]


    #
    #  ssNav - single square navigate, turn and move to position, h,
    #          which should be an adjacent square.
    #

    def ssNav (self, vel, dist, h):
        self.reset ()
        initpos = self.d2pv (self.getpos (self.me ()))
        count = 0
        mypos = self.d2pv (self.getpos (self.me ()))
        while (dist > 0) and (not equVec (h, mypos)):
            print("bot at", mypos, "trying to reach", h)
            mydoom = self.twoDdoom (self.getpos (self.me ()))
            hdoom = self.midPen2Doom (h)
            self.turnface (subVec (hdoom, mydoom))
            self.select (["turn"])
            if debugging:
                print("completed turn along", subVec (h, mypos))
            if dist > self.p2d (1)/2:
                d = self.p2d (1)/2
            else:
                d = dist
            self.forward (vel, d)
            self.select (["move"])
            if debugging:
                print("completed forward", d, "units")
            # time.sleep (2)
            self.reset ()
            dist -= d
            mypos = self.d2pv (self.getpos (self.me ()))
            if equVec (initpos, mypos):
                if debugging:
                    print("not moved substantially")
                count += 1
                if count == 4:
                    if debugging:
                        print("stuck, try again")
                    self.runArc (random.randint (0, 360), 100)  # random turn and run 100 inches
                    return dist

        if debugging:
            if equVec (h, mypos):
                print("bot has reached", h, "!!")
        return dist


    #
    #  ssBulkNav - multiple square navigate, turn and move to position, h.
    #

    def ssBulkNav (self, vel, h, noHops):
        self.reset ()
        initpos = self.d2pv (self.getpos (self.me ()))
        count = 0
        mypos = self.d2pv (self.getpos (self.me ()))
        d = 0
        dist = 0
        if debugging:
            print("bot at", mypos, "trying to reach", h)
        mydoom = self.twoDdoom (self.getpos (self.me ()))
        hdoom = self.midPen2Doom (h)
        self.turnface (subVec (hdoom, mydoom))
        self.select (["turn"])
        if debugging:
            print("completed turn along", subVec (h, mypos))
        d = self.p2d (noHops)/2
        # d = sqrt (sqr (mydoom[0] - hdoom[0]) + sqr (mydoom[1] - hdoom[1]))
        self.forward (vel, d)
        self.select (["move"])
        if debugging:
            print("completed forward", d, "units")
        self.reset ()
        mypos = self.d2pv (self.getpos (self.me ()))
        if equVec (initpos, mypos):
            if debugging:
                print("not moved substantially")
            count += 1
            if count == 4:
                if debugging:
                    print("stuck, try again")
                self.runArc (random.randint (0, 360), 100)  # random turn and run 100 inches
                return 0
        dist += d
        if debugging:
            if equVec (h, mypos):
                print("bot has reached", h, "!!")
        return dist

    #
    #
    #

    def twoDdoom (self, v):
        if len (v) > 2:
            v = v[:2]
        return negVec (v)


    #
    #  face - turn to face object, i.  If we are close we attempt to aim
    #         at object.
    #

    def face (self, i):
        self.reset ()
        p = self.twoDdoom (self.getpos (self.me ()))
        h = self.twoDdoom (self.getpos (i))
        self.turnface (subVec (h, p))
        self.select (["turn"])
        self.sync ()
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
