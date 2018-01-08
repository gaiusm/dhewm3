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

from array2d import array2d
from chvec import *
from botutils import *

import sys
import os
initMapSize = 1


mapdir = os.path.join (os.environ['HOME'], ".local/share/dhewm3/base/maps")
debugging = False
debugroute = True

status_open, status_closed, status_secret = range (3)
rooms = {}           #  dictionary of rooms
maxx, maxy = 0, 0    #  the size of our map
INFINITY = 1000000   #  must be bigger than all computed distance costs
wallCost = 0         #  a number used to represent the cost of going through a wall

class roomInfo:
    def __init__ (self, r, w, d):
        self.walls = w
        self.doors = d
        self.doorLeadsTo = []
        self.pythonMonsters = []
        self.monsters = []
        self.weapons = []
        self.ammo = []
        self.lights = []
        self.worldspawn = []
    def _addWall (self, line):
        global maxx, maxy
        line = toLine (line)
        self.walls += [line]
        maxx = max (line[0][0], maxx)
        maxx = max (line[1][0], maxx)
        maxy = max (line[0][1], maxy)
        maxy = max (line[1][1], maxy)
    def _addDoor (self, line, leadsto, status):
        self.doors += [[toLine (line), leadsto, status]]
    def _addAmmo (self, ammoType, ammoAmount, ammoPos):
        self.ammo += [[ammoType, ammoAmount, ammoPos]]
    def _addLight (self, pos):
        self.lights += [intVec (pos)]
    def _addWeapon (self, weapon, pos):
        self.weapons += [[weapon, pos]]
    def _addPythonMonster (self, monType, pos):
        self.pythonMonsters += [[monType, pos]]
    def _addMonster (self, monType, pos):
        self.monsters += [[monType, pos]]
    def _addPlayerSpawn (self, pos):
        self.worldspawn += [pos]


#
#  isVertical - return True if, c, is a vertical line.
#

def isVertical (c):
    return c[0][0] == c[1][0]


#
#  isHorizontal - return True if, c, is a horizontal line.
#

def isHorizontal (c):
    return c[0][1] == c[1][1]

#
#  toLine - returns a list containing two coordinates.
#           input:  a list of two coordinates in ascii
#           output: a list of two integer coordinates the lower or left
#                   coordinate will be the first coordinate.
#

def toLine (l):
    l = [[int (l[0][0]), int (l[0][1])], [int (l[1][0]), int (l[1][1])]]
    return _sortWall (l)

#
#  sortWall - order a wall coordinate left, bottom to right, top
#

def _sortWall (w):
    if debugging:
        print "sortwall", w
    if isVertical (w):
        if w[0][1] > w[1][1]:
            return [w[1], w[0]]
        return w
    if isHorizontal (w):
        if w[0][0] > w[1][0]:
            return [w[1], w[0]]
        return w
    print "wall problem", w
    internalError ('wall must be horizontal or vertical')


def newRoom (n):
    global rooms
    if rooms.has_key (n):
        error ("room " + n + " has already been defined")
    rooms[n] = roomInfo (n, [], [])
    return rooms[n]


#
#  Area awareness code follows
#

class aas:
    def __init__ (self, mapname):
        self._verbose = False
        self._route = []
        self._floor = array2d (initMapSize, initMapSize, ' ')
        self._weightings = array2d (initMapSize, initMapSize, [1])
        self._currentLineNo = 1
        self._loadMap (mapname)
        self._recreateFloor (None)
        self._calcWeightings ()

    #
    #  _drawLine -
    #

    def _drawLine (self, w, c):
        if isVertical (w):
            for y in range (w[0][1], w[1][1]+1):
                self._floor.set (w[0][0], y, c)
        else:
            for x in range (w[0][0], w[1][0]+1):
                self._floor.set (x, w[0][1], c)

    #
    #  _weightLine -
    #

    def _weightLine (self, w, c):
        if isVertical (w):
            for y in range (w[0][1], w[1][1]+1):
                self._weightings.set (w[0][0], y, c)
        else:
            for x in range (w[0][0], w[1][0]+1):
                self._weightings.set (x, w[0][1], c)


    #
    #  recreateFloor - delete the current floor
    #                  and recreate it with current knowledge.
    #

    def _recreateFloor (self, b):
        del self._floor
        self._floor = array2d (initMapSize, initMapSize, ' ')
        for r in rooms.keys ():
            for w in rooms[r].walls:
                self._drawLine (w, '#')
            for d in rooms[r].doors:
                self._drawLine (d[0], ' ')
            for l in rooms[r].lights:
                print l
                self._floor.set (l[0], l[1], 'l')
        self.printFloor ()
        if b != None:
            self._updateEntities (b)

    #
    #  updateKnowlege - generate a floor map with all static and dynamic entities
    #                   placed on it.
    #

    def updateKnowlege (self, b):
        self._recreateFloor (b)


    #
    #  _calcWeightings - calculate the movement cost matrix for all the area.
    #                    It chooses cost of 1 to move a square and represents
    #                    walls by wallCost.
    #

    def _calcWeightings (self):
        del self._weightings
        self._weightings = array2d (self._floor.high ()[0], self._floor.high ()[1], [1])
        for r in rooms.keys ():
            for w in rooms[r].walls:
                self._weightLine (w, [wallCost])
            for d in rooms[r].doors:
                self._weightLine (d[0], [1])
            for l in rooms[r].lights:
                self._weightings.set (l[0], l[1], [wallCost])
        self.printWeightings ()

    #
    #  updateEntities - add movable and fixed entities to our aa map.
    #

    def _updateEntities (self, b):
        self._entities = []
        for e in range (b.maxobj ()):
            pass

    def printXaxis (self, top):
        if not top:
            s = "  +" + self._floor.high ()[0] * "-"
            printf ("%s-+\n", s)
        s = "   "
        for i in range (self._floor.high ()[0]):
            if i % 10 == 0:
                s += "%d" % (i / 10)
            else:
                s += " "
        printf ("%s\n", s)
        if top:
            s = "  +" + self._floor.high ()[0] * "-"
            printf ("%s-+\n", s)

    #
    #  inRoute - return True if pos is in the current route.
    #

    def inRoute (self, pos):
        for p in self._route:
            if equVec (p, pos):
                return True
        return False

    #
    #  printFloor - print out the floor plan of the map
    #

    def printFloor (self, src = None, dest = None):
        self.printXaxis (True)
        yaxis = range (self._floor.high ()[1])
        yaxis.reverse ()
        for j in yaxis:
            s = "%2d" % j
            s += "|"
            for i in range (self._floor.high ()[0]):
                curpos = [i, j]
                if (src != None) and equVec (curpos, src):
                    s += 'S'
                elif (dest != None) and equVec (curpos, dest):
                    s += 'E'
                elif self.inRoute (curpos):
                    s += '*'
                else:
                    s += self._floor.get (i, j)
            s += " |"
            s += "%2d" % j
            printf ("%s\n", s)
        self.printXaxis (False)


    #
    #  printWeightings - print out the floor weighings of the map
    #

    def printWeightings (self):
        self.printXaxis (True)
        yaxis = range (self._floor.high ()[1])
        yaxis.reverse ()
        for j in yaxis:
            s = "%2d" % j
            s += "|"
            for i in range (self._floor.high ()[0]):
                if self._weightings.get (i, j) == 0:
                    s += '0'
                else:
                    s += '1'
            printf ("%s\n", s)
        self.printXaxis (False)


    #
    #  lexicalPen - return a list of tokens to be read by the parser.
    #               A special token <eoln> is added at the end of each line.
    #               <eof> is added at the end.
    #

    def lexicalPen (self, i):
        words = []
        for l in i.readlines ():
            w = l.split ()
            w += ['<eoln>']
            for j in w:
                if j != "":
                    i = j.rstrip ()
                    words += [i]
            words += ['<eof>']
        return words

    #
    #  _loadMap - internal method which is run when the constructor
    #             is initiated.
    #

    def _loadMap (self, mapname):
        self._filename = os.path.join (mapdir, mapname)
        print "need to read in", self._filename
        self.words = self.lexicalPen (open (self._filename, 'r'))
        self.parsePen ()

    #
    #  errorLine - issue an error message using the filename and line of error.
    #

    def errorLine (self, text):
        full = "%s:%d:%s\n" % (self._filename, self._currentLineNo, text)
        print full,

    #
    #  doGetToken - return the first word and remaining words.
    #               return car, cdr
    #               at a mimimum cdr will always contain ['<eof>']
    #

    def doGetToken (self):
        if len (self.words) > 1:
            return self.words[0], self.words[1:]
        elif len (self.words) == 1:
            return self.words[0], ['<eof>']


    def expectEoln (self):
        if self.words[0] == '<eoln>':
            self._currentLineNo += 1
            self.words = self.words[1:]


    #
    #  get - returns the next token and the remainder of the words.
    #

    def get (self):
        n, self.words = self.doGetToken ()
        while n == '<eoln>':
            self.expectEoln ()
            n, self.words = self.doGetToken ()
        return n


    #
    #  peek - returns the first token without removing it from input.
    #         It will advance the linenumber if <eoln> is seen.
    #

    def peek (self):
        n = self.words[0]
        while n == '<eoln>':
            self.expectEoln ()
            return self.peek ()
        return n


    #
    #  expect - expect a token, t.
    #

    def expect (self, t):
        g = self.get ()
        if g != t:
            self.errorLine ('expecting ' + t + ' and seen ' + g)


    #
    #  expecting - return True if the next token is one of, l.
    #

    def expecting (self, l):
        t = self.peek ()
        return t in l


    #
    #  lexicalPen - return a list of tokens to be read by the parser.
    #               A special token <eoln> is added at the end of each line.
    #               <eof> is added at the end.
    #

    def lexicalPen (self, i):
        self.words = []
        for l in i.readlines ():
            w = l.split ()
            w += ['<eoln>']
            for j in w:
                if j != "":
                    i = j.rstrip ()
                    self.words += [i]
        self.words += ['<eof>']
        return self.words


    #
    #  wallCoord - return True if four numbers were seen
    #

    def wallCoords (self):
        if self.integer ():
            x0 = self._curInteger
            if self.integer ():
                y0 = self._curInteger
                if self.integer ():
                    x1 = self._curInteger
                    if self.integer ():
                        y1 = self._curInteger
                        self._curRoom._addWall ([[x0, y0], [x1, y1]])
                        return True
                    else:
                        self.errorLine ('expecting fourth integer for a wall')
                else:
                    self.errorLine ('expecting third integer for a wall')
            else:
                self.errorLine ('expecting second integer for a wall')
        return False


    #
    #  wallDesc :- 'WALL' wallCoords { wallCoords } -:
    #

    def wallDesc (self):
        self.expect ('WALL')
        if self.wallCoords ():
            while self.wallCoords ():
                pass


    #
    #  status := "STATUS" ( [ 'OPEN' | 'CLOSED' | 'SECRET' ] ) =:
    #

    def status (self):
        self.expect ('STATUS')
        if self.expecting (['OPEN', 'CLOSED', 'SECRET']):
            if self.expecting (['OPEN']):
                self.curStatus = status_open
                self.expect ('OPEN')
            elif expecting (['CLOSED']):
                self.curStatus = status_closed
                self.curStatus = status_open    # --fixme-- closed doors would be nice!
                self.expect ('CLOSED')
            elif expecting (['SECRET']):
                self.curStatus = status_secret
                self.curStatus = status_open    # --fixme-- secret doors would be nice!
                self.expect ('SECRET')
            return True
        return False


    #
    #  integer - if the next token is an integer then
    #               consume it and save it into curInteger
    #               return True
    #            else:
    #               return False
    #

    def integer (self):
        i = self.peek ()
        if i.isdigit ():
            self._curInteger = self.get ()
            return True
        return False


    #
    #  doorCoords := integer integer integer integer status "LEADS" "TO" integer =:
    #

    def doorCoords (self):
        if self.integer ():
            x0 = self._curInteger
            if self.integer ():
                y0 = self._curInteger
                if self.integer ():
                    x1 = self._curInteger
                    if self.integer ():
                        y1 = self._curInteger
                        if self.status ():
                            self.expect ("LEADS")
                            self.expect ("TO")
                            if self.integer ():
                                leadsTo = self._curInteger
                                self._curRoom._addDoor ([[x0, y0], [x1, y1]], leadsTo, self.curStatus)
                                return True
                    else:
                        self.errorLine ('expecting fourth integer for a wall')
                else:
                    self.errorLine ('expecting third integer for a wall')
            else:
                self.errorLine ('expecting second integer for a wall')
        return False


    #
    #  doorDesc := "DOOR" doorCoords { doorCoords } =:
    #

    def doorDesc (self):
        self.expect ('DOOR')
        if self.doorCoords ():
            while self.doorCoords ():
                pass
            return True
        return False


    #
    #  posDesc := integer integer =:
    #

    def posDesc (self):
        global curPos
        if self.integer ():
            x = self._curInteger
            if self.integer ():
                curPos = [x, self._curInteger]
                return True
            else:
                self.errorLine ('expecting second integer in the position pair')
        return False


    #
    #  ammoDesc := "AMMO" integer "AMOUNT" integer "AT" posDesc =:
    #

    def ammoDesc (self):
        self.expect ('AMMO')
        ammoType = self.get ()
        self.expect ('AMOUNT')
        if self.integer ():
            ammoAmount = self._curInteger
            self.expect ('AT')
            if self.posDesc ():
                ammoPos = curPos
                self._curRoom._addAmmo (ammoType, ammoAmount, ammoPos)
            else:
                self.errorLine ('expecting a position for the ammo')
        else:
            self.errorLine ('expecting an amount of ammo')

    #
    #  lightOn := 'ON' type =:
    #

    def lightOn (self):
        self.expect ('ON')
        if self.expecting (['FLOOR']):
            self.expect ('FLOOR')
        elif self.expecting (['CEIL']):
            self.expect ('CEIL')
        elif self.expecting (['MID']):
            self.expect ('MID')
            self._curRoom._addLight (curPos)
        else:
            self.errorLine ('expecting FLOOR or CEIL or MID after ON in LIGHT description')


    #
    #  lightDesc := 'LIGHT' 'AT' posDesc =:
    #

    def lightDesc (self):
        self.expect ('LIGHT')
        self.expect ('AT')
        if self.posDesc ():
            if self.expecting (['ON']):
                self.lightOn ()
            else:
                # default to MID light so add the light pillar
                self._curRoom._addLight (curPos)
            return True
        else:
            self.errorLine ('expecting a position for a light')
            return False


    #
    #  weaponDesc := 'LIGHT' 'AT' posDesc =:
    #

    def weaponDesc (self):
        self.expect ('WEAPON')
        if self.integer ():
            weapon = self._curInteger
            self.expect ('AT')
            if self.posDesc ():
                self._curRoom._addWeapon (weapon, curPos)
                return True
            else:
                self.errorLine ('expecting a position for a weapon')
        else:
            self.errorLine ('expecting a weapon number')
        return False


    #
    #  monsterDesc := 'MONSTER' type 'AT' posDesc =:
    #

    def monsterDesc (self):
        self.expect ('MONSTER')
        monType = self.get ()
        self.expect ('AT')
        if self.posDesc ():
            if (len (monType) > len ("python_")) and ("python_" == monType[:len ("python_")]):
                self._curRoom._addPythonMonster (monType, curPos)
            else:
                self._curRoom._addMonster (monType, curPos)
            return True
        else:
            self.errorLine ('expecting a position for a monster')
        return False


    def spawnDesc (self):
        self.expect ('SPAWN')
        self.expect ('PLAYER')
        self.expect ('AT')
        if self.posDesc ():
            self._curRoom._addPlayerSpawn (curPos)
            return True
        else:
            self.errorLine ('expecting a position for a player spawn')
        return False

    #
    #  insideDesc := 'INSIDE' 'AT' Pos
    #

    def insideDesc (self):
        self.expect ('INSIDE')
        self.expect ('AT')
        return self.posDesc ()

    #
    #  colourDesc - int int int
    #

    def colourDesc (self):
        if self.integer ():
            if self.integer ():
                if self.integer ():
                    return True
        return False


    #
    #  defaultDesc := 'DEFAULT' ['MID' | 'CEIL' | 'FLOOR']
    #

    def defaultDesc (self):
        self.expect ('DEFAULT')
        if self.expecting (['MID']):
            self.expect ('MID')
        elif self.expecting (['CEIL']):
            self.expect ('CEIL')
        elif self.expecting (['FLOOR']):
            self.expect ('FLOOR')
        self.expect ('COLOUR')
        return self.colourDesc ()


    #
    #  roomDesc := "ROOM" integer { doorDesc | wallDesc | treasureDesc | ammoDesc | lightDesc | weaponDesc | monsterDesc | spawnDesc | insideDesc } =:
    #

    def roomDesc (self):
        if self.expecting (['ROOM']):
            self.expect ("ROOM")
            if self.integer ():
                self._curRoomNo = self._curInteger
                self._curRoom = newRoom (self._curRoomNo)
                if self._verbose:
                    print "roomDesc", curRoomNo
                while self.expecting (['DOOR', 'WALL', 'TREASURE', 'AMMO', 'WEAPON', 'LIGHT', 'MONSTER', 'SPAWN', 'INSIDE', 'DEFAULT']):
                    if self.expecting (['DOOR']):
                        self.doorDesc ()
                    elif self.expecting (['WALL']):
                        self.wallDesc ()
                    elif self.expecting (['TREASURE']):
                        self.treasureDesc ()
                    elif self.expecting (['AMMO']):
                        self.ammoDesc ()
                    elif self.expecting (['WEAPON']):
                        self.weaponDesc ()
                    elif self.expecting (['LIGHT']):
                        self.lightDesc ()
                    elif self.expecting (['WEAPON']):
                        self.weaponDesc ()
                    elif self.expecting (['MONSTER']):
                        self.monsterDesc ()
                    elif self.expecting (['SPAWN']):
                        self.spawnDesc ()
                    elif self.expecting (['INSIDE']):
                        self.insideDesc ()
                    elif self.expecting (['DEFAULT']):
                        self.defaultDesc ()
                self.expect ('END')
                return True
            else:
                self.errorLine ('expecting an integer after ROOM')
        return False


    #
    #  parsePen := roomDesc { roomDesc } randomTreasure "END." =:
    #

    def parsePen (self):
        if self.roomDesc ():
            while self.roomDesc ():
                pass
            # if randomTreasure ():
            #    pass
            self.expect ("END.")
            return True
        return False

    #
    #  checkLegal - pos is checked to make sure it is not on a wall.
    #

    def checkLegal (self, pos, message):
        if self._floor.get (pos[0], pos[1]) == '#':
            print "error", message, "position", pos, "is a wall"
            sys.exit (1)

    #
    #  calcnav - calculate the navigation route between us and object, d.
    #            No movement is done, it only works out the best route.
    #            This is quite expensive and should be used sparingly.
    #            It returns the total distance between ourself and
    #            object, d, assuming this route was followed.  Notice
    #            this is not the same as a line of sight distance.
    #            The distance returned is a doom3 unit.
    #

    def calcnav (self, src, dest):
        self._neighbours = {}
        self._cost = {}
        self._prev = {}
        self._route = []
        self._choices = [src]
        self._setCostRoute (src, 1, src)
        self._visited = []
        print "src =", src, "dest =", dest
        self.checkLegal (src, "source")
        self.checkLegal (dest, "destination")
        if equVec (src, dest):
            self._route = [dest]
            return 0
        while self._choices != []:
            if debugroute:
                print "we have the following nodes to explore:", self._choices
            u = self._getBestChoice ()
            self._visited += [u]
            if debugroute:
                print "have chosen", u, "cost from src is", self._getCost (u)
            if equVec (u, dest):
                if debugroute:
                    print "found end of route"
                self._route = self._defineRoute (src, dest)
                if debugroute:
                    self.printFloor (src, dest)
                return self._getCost (dest)
            for v in self._getNeighbours (u):
                self._addChoice (v)
                print "at", u, "checking step", v,
                alternative = self._getCost (u) + self._getLength (v)
                print "cost", alternative, "was", self._getCost (v)
                if alternative >= INFINITY:
                    print "bug in dijkstra", alternative, "should not exceed infinity"
                if alternative < self._getCost (v):
                    if debugroute:
                        print "found a better route to '", v, "' value", alternative, "from '", src, "'"
                    self._setCostRoute (v, alternative, u)
        print "unable to find a route from", src, "to", dest
        return None


    def _setCostRoute (self, n, cost, prev):
        k = '%d_%d' % (n[0], n[1])
        if debugroute:
            print 'cost[', k, '] =', cost, 'prev =', prev, '_prev[', k, '] =', prev
        self._cost[k] = cost
        self._prev[k] = prev


    #
    #  defineRoute - build a list of previous entries from dest, back to src.
    #

    def _defineRoute (self, src, dest):
        print "route from", src, "to", dest, "is",
        r = [dest]
        while src != dest:
            k = '%d_%d' % (dest[0], dest[1])
            dest = self._prev[k]
            r += [dest]
        r.reverse ()
        print r
        return r


    #
    #  noOfHops - return the number of hops.
    #

    def noOfHops (self):
        return len (self._route)

    #
    #  getHop - return the location of the, hop, square used in the route.
    #           return route[hop]   (which will be a 2d coordinate)
    #

    def getHop (self, hop):
        if hop > len (self._route):
            return self._route[-1]
        return self._route[hop]


    #
    #  removeHop - in:  index, i, into the journey route.  p, coordinate.
    #              out:  if p is at position, i, and the journey has more than
    #                    one step then this step is removed.
    #

    def removeHop (self, i, p):
        if (len (self._route) > 1) and (i < len (self._route)):
            if equVec (p, self._route[i]):
                del self._route[i]


    #
    #  addChoice - adds a unique choice to the choices list
    #

    def _addChoice (self, c):
        print "choices =", self._choices
        print "visited =", self._visited
        if len (self._choices) > 0:
            for i in self._choices:
                if equVec (i, c):
                    return
        if len (self._visited) > 0:
            for i in self._visited:
                if equVec (i, c):
                    return
        self._choices += [c]


    #
    #  getBestChoice - return the lowest choice cost
    #

    def _getBestChoice (self):
        c = self._choices[0]
        cost = self._getCost (c)
        if len (self._choices) > 0:
            z = 0
            for x, i in  enumerate (self._choices[1:]):
                if self._getCost (i) < cost:
                    c = i
                    cost = self._getCost (c)
                    z = x
            del self._choices[z]
        else:
            self._choices = []
        return c


    #
    #  getCost - return the cost of moving to position, p.
    #

    def _getCost (self, p):
        k = '%d_%d' % (p[0], p[1])
        if not self._cost.has_key (k):
            if debugroute:
                print "no cost entry, setting to infinity", k
            self._cost[k] = INFINITY
        return self._cost[k]


    #
    #  _getLength - return the
    #

    def _getLength (self, p):
        if self._weightings.get (p[0], p[1]) == wallCost:
            return INFINITY
        f = self._weightings.get (p[0], p[1])
        return f


    #
    #  clearOfObstacle - return True if no wall or light occupies location, v.
    #

    def clearOfObstacle (self, v):
        return (self._floor.get (v[0], v[1]) != '#') and (self._floor.get (v[0], v[1]) != 'l')

    #
    #  _getNeighbours - returns the neighbours of, p.
    #

    def _getNeighbours (self, p):
        k = '%d_%d' % (p[0], p[1])
        if not self._neighbours.has_key (k):
            n = []
            # south, east, west, north
            for v in [[-1, 0], [1, 0], [0, -1], [0, 1]]:
                w = addVec (p, v)
                if self._weightings.inRange (w[0], w[1]) and (self._weightings.get (w[0], w[1]) != wallCost):
                    n += [w]
            # now the diagonals so long as the two square either side are also free
            for v in [[[-1, -1], [-1, 0], [0, -1]],
                      [[-1,  1], [-1, 0], [0,  1]],
                      [[ 1,  1], [ 1, 0], [0,  1]],
                      [[ 1, -1], [ 1, 0], [0, -1]]]:
                d = addVec (p, v[0])
                a = addVec (p, v[1])
                b = addVec (p, v[2])
                if (self._weightings.inRange (d[0], d[1]) and self.clearOfObstacle (d) and self.clearOfObstacle (a) and self.clearOfObstacle (b)):
                    n += [d]
            self._neighbours[k] = n
        return self._neighbours[k]


    #
    #  getPlayerStart - returns the pen coordinates of the initial spawn point
    #                   of the human player.
    #

    def getPlayerStart (self):
        for r in rooms.keys ():
            if rooms[r].worldspawn != []:
                return rooms[r].worldspawn[0]
        print "the pen map should contain one worldspawn location"
        print "this needs to be fixed before area awareness makes any sence to the bot"
        return [1, 1]


#
#  intVec - return a vector of two integers.
#

def intVec (v):
    return [int (v[0]), int (v[1])]


def _runtests ():
    print "hello"
    m = aas (os.path.join (os.path.join (os.environ['HOME'], ".local/share/dhewm3/base/maps"),
                           "tiny.pen"))
    src = intVec (rooms['1'].pythonMonsters[0][1])
    dest = intVec (rooms['3'].worldspawn[0])
    m.printFloor (src, dest)
    c = m.calcnav (src, dest)
    print "cost =", c
    print m._route
    m.printFloor (src, dest)


if __name__ == "__main__":
    _runtests ()
