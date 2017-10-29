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

from botutils import *
from socket import *

superServer = 7000
debug_protocol = True


#
#  tovecint - convert a string of numbers into a list of ints.
#

def tovecint (l):
    n = []
    for i in l.split (' '):
        n += [int (i)]
    return n


class basic:
    #
    #  __init__ the constructor for class bot which
    #           connects to the superserver to find out
    #           the bot port.  It then connects to the
    #           bot port.
    #

    def __init__ (self, server, name):
        global superServer
        while True:
            self.s = self.connectSS (server)
            #
            #  firstly we need to double check the superServer is on this port
            #  as a quick rerun of the game might have forced a different portno.
            #  The bot server will also know the superServer port and will tell us
            #  the port of the superServer.
            #
            self.s.send ('super\n')
            p = int (self.getPort ())
            print superServer, p
            if p == superServer:
                print "successfully double checked the superserver port"
                self.s.close ()             # all done with that connection,
                # we reconnect and go for the real bot request.
                self.s = self.connectSS (server)
                #
                #  all good, we now ask it about the botserver portno
                #
                print "sending botname request to superserver", name
                self.s.send (name + '\n')   # specific botserver requested
                print "waiting for port reply from superserver", name
                p = int (self.getPort ())
                print "about to close this socket", name
                self.s.close ()             # all done with the superServer
                if p != 0:
                    print "found botname", name, "port is", p
                    break                   # found the portno
                #
                #  at this point the bot server is not ready
                #  so we need to wait and try again.
                #
                time.sleep (1)
            else:
                self.s.close ()             # all done with this server
                superServer = p             # superServer has moved portno
                print "superserver has changed port to", p
        self.s = self.connectBot (server, p, name)
        self._maxX = None
        self._maxY = None


    #
    #  connectSS - connects to the superserver
    #

    def connectSS (self, server):
        global superServer
        print "bot trying to connect to the superserver on port", superServer
        i = 0
        while True:
            for j in range (10):
                success, s = self.tryConnectSS (server, superServer+j)
                if success:
                    superServer = superServer+j
                    print "bot connected to superserver on port", superServer
                    return s
            sys.stdout.write (".")
            sys.stdout.flush ()
            time.sleep (2)

    #
    #  tryConnectSS - tries to make a connection to server:port
    #                 It returns a pair: bool, socket.
    #

    def tryConnectSS (self, server, port):
        try:
            s = socket (AF_INET, SOCK_STREAM)
            s.connect ((server, port))
            return True, s
        except:
            return False, None

    #
    #  getPort - returns the portNo from the superserver.
    #

    def getPort (self):
        return self.getLine ()

    #
    #  getLine - read a character at a time until \n is seen.
    #

    def getLine (self):
        l = ""
        while True:
            c = self.s.recv (1)
            if c == '\n':
                break
            l += c
        if debug_protocol:
            print "<socket has sent>", l
        return l

    #
    #  connectBot - connects to the bot server
    #

    def connectBot (self, server, port, name):
        s = socket (AF_INET, SOCK_STREAM)
        print "python bot trying to connect to the bot server", port, name
        i = 0
        while True:
            try:
                s.connect ((server, port))
                break
            except:
                print ".",
                sys.stdout.flush ()
                time.sleep (1)
        print "bot connected to bot server"
        return s


    #
    #  line2vec - in:   a string of three numbers space separated.
    #             out:  returns a list of three integers.
    #

    def line2vec (self, l):
        print "line2vec", l
        v = []
        for w in l.split ():
            print w
            v += [int (float (w))]
        return v


    #
    #  getpos - makes a request to the doom3 server to find the
    #           location of, obj.
    #           returns a list [x, y, z] values
    #           (units are doom3 units).
    #

    def getpos (self, obj):
        l = "getpos %d\n" % (obj)
        if debug_protocol:
            print "getpos command:", l
        self.s.send (l)
        return self.line2vec (self.getLine ())


    #
    #  me - return the id of this bot.
    #

    def me (self):
        self.s.send ("self\n")
        return int (self.getLine ())


    #
    #  maxobj - return the maximum number of registered, ids in the game.
    #           Each monster, player, ammo pickup has an id
    #

    def maxobj (self):
        self.s.send ("maxobj\n")
        return int (self.getLine ())


    #
    #  objectname - return the name of the object, d.
    #  (not yet implemented in the doom3 server)

    def objectname (self, d):
        l = "objectname %d\n" % (d)
        self.s.send (l)
        return self.getLine ()


    #
    #  isvisible - return True if object, d, is line of sight visible.
    #  (not implemented yet)
    #

    def isvisible (self, d):
        return False


    #
    #  isfixed - return True if the object is a static fixture in the map.
    #  (not implemented yet)
    #

    def isfixed (self, d):
        return False


    #
    #  right - step right at velocity, vel, for dist, units.
    #

    def right (self, vel, dist):
        v = int (vel)
        d = int (dist)
        l = "right %d %d\n" % (v, d)
        if debug_protocol:
            print "requesting a right step", v, d
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)

    #
    #  forward - step forward at velocity, vel, for dist, units.
    #

    def forward (self, vel, dist):
        v = int (vel)
        d = int (dist)
        l = "forward %d %d\n" % (v, d)
        if debug_protocol:
            print "requesting a forward step", v, d
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)


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
    #  stepvec - step along a vector at velocity [velforward, velright] for a, dist.
    #

    def stepvec (self, velforward, velright, dist):
        f = int (velforward)
        r = int (velright)
        d = int (dist)
        l = "stepvec %d %d %d\n" % (f, r, d)
        if debug_protocol:
            print "requesting a forward step", f, r, d
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)


    #
    #  sync - wait for one event to finish.
    #         The event will signify the end of any of the following:
    #         ['move', 'fire', 'turn', 'reload'].
    #

    def sync (self):
        if debug_protocol:
            print "requesting sync"
        self.s.send ("select any\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return l

    #
    #  select - wait for any desired event:  legal events are
    #           ['move', 'fire', 'turn', 'reload'].
    #

    def select (self, l):
        b = 0
        for w in l:
            if w == 'move':
                b += 1
            elif w == 'fire':
                b += 2
            elif w == 'turn':
                b += 4
            elif w == 'reload':
                b += 8
            else:
                printf ("incorrect parameter to select (%s)\n", w)
        l = "select %d\n" % (b)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)


    #
    #  startFiring - fire weapon
    #                It returns the amount of ammo left.
    #

    def startFiring (self):
        if debug_protocol:
            print "requesting to fire weapon"
        self.s.send ("start_firing\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)


    #
    #  stopFiring - stop firing weapon
    #                It returns the amount of ammo left.
    #

    def stopFiring (self):
        if debug_protocol:
            print "requesting to stop firing weapon"
        self.s.send ("stop_firing\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)


    #
    #  reloadWeapon - reload the current weapon
    #                  It returns the amount of ammo left.
    #

    def reloadWeapon (self):
        if debug_protocol:
            print "requesting to reload weapon"
        self.s.send ("reload_weapon\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)

    #
    #  ammo - returns the amount of ammo for the current weapon.
    #

    def ammo (self):
        if debug_protocol:
            print "requesting ammo"
        self.s.send ("ammo\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)

    #
    #  aim - aim weapon at player, i
    #

    def aim (self, i):
        if debug_protocol:
            print "requesting aim at", i
        l = "aim %d\n" % (i)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return l == 'true'

    #
    #  turn - turn to face, angle.
    #

    def turn (self, angle, angle_vel):
        if debug_protocol:
            print "requesting turn ", angle, angle_vel
        l = "turn %d %d\n" % (angle, angle_vel)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return l == 'true'

    #
    #  getPenMapName - return the name of the current pen map.
    #

    def getPenMapName (self):
        if debug_protocol:
            print "requesting penmap"
        self.s.send ("penmap\n")
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return l

    #
    #  getClassNameEntity - return the first entity number containing, "name".
    #                       This is used by botlib (it looks up "penmap").
    #

    def getClassNameEntity (self, name):
        if debug_protocol:
            print "requesting getclassnameentity"
        l = "get_class_name_entity %s\n" % (name)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)

    #
    #  getPairEntity - return the entity contain the pair of strings.
    #                  left, right.
    #

    def getPairEntity (self, left, right):
        if debug_protocol:
            print "requesting get_pair_name_entity", left, right
        l = "get_pair_name_entity %s %s\n" % (left, right)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return int (l)

    #
    #  getPlayerStart - returns the player start location.
    #

    def getPlayerStart (self):
        return self.getEntityPos (self.getPairEntity ("classname", "info_player_start"))

    #
    #  getEntityPos - returns coordinate representating the origin position of entity, i.
    #

    def getEntityPos (self, i):
        if debug_protocol:
            print "requesting get_entity_pos", i
        l = "get_entity_pos %d\n" % (i)
        self.s.send (l)
        l = self.getLine ()
        if debug_protocol:
            print "doom returned", l
        return tovecint (l)

    #
    #  reset - does nothing and its only purpose is to provide a similar
    #          api as the botcache and botlib layers.
    #

    def reset (self):
        pass

    #
    #  allobj - return a list of all objects
    #

    def allobj (self):
        return range (1, self.maxobj () + 1)
