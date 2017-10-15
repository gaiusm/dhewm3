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
import sys
import os
initMapSize = 1

mapdir = os.path.join (os.environ['HOME'], ".local/share/dhewm3/base/maps")
debugging = False


status_open, status_closed, status_secret = range (3)
rooms = {}         # dictionary of rooms
maxx, maxy = 0, 0  #  the size of our map


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print str(format) % args,


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
        self.lights += [pos]
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
        self._rooms = {}
        self._floor = array2d (initMapSize, initMapSize, ' ')
        self._weightings = array2d (initMapSize, initMapSize, [1])        
        self._currentLineNo = 1
        self._loadMap (mapname)
        self._recreateFloor ()
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

    def _recreateFloor (self):
        del self._floor
        self._floor = array2d (initMapSize, initMapSize, ' ')
        for r in rooms.keys ():
            for w in rooms[r].walls:
                self._drawLine (w, '#')
            for d in rooms[r].doors:
                self._drawLine (d[0], ' ')
        self.printFloor ()

    def _calcWeightings (self):
        del self._weightings
        self._weightings = array2d (self._floor.high ()[0], self._floor.high ()[1], [1])
        for r in rooms.keys ():
            for w in rooms[r].walls:
                self._weightLine (w, [0])
            for d in rooms[r].doors:
                self._weightLine (d[0], [1])
        self.printWeightings ()                        
        
    #
    #  printFloor - print out the floor plan of the map
    #

    def printFloor (self):
        for j in range (self._floor.high ()[1]):
            s = ""
            for i in range (self._floor.high ()[0]):
                s += self._floor.get (i, j)
            printf ("%s\n", s)

            
    #
    #  printWeightings - print out the floor weighings of the map
    #

    def printWeightings (self):
        for j in range (self._weightings.high ()[1]):
            for i in range (self._weightings.high ()[0]):
                if self._weightings.get (i, j) == 0:
                    sys.stdout.write ('0')
                else:
                    sys.stdout.write ('1')
            printf ("\n")
    
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
    #  lightDesc := 'LIGHT' 'AT' posDesc =:
    #

    def lightDesc (self):
        self.expect ('LIGHT')
        self.expect ('AT')
        if self.posDesc ():
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
    #  roomDesc := "ROOM" integer { doorDesc | wallDesc | treasureDesc | ammoDesc | lightDesc | weaponDesc | monsterDesc | spawnDesc } =:
    #

    def roomDesc (self):
        if self.expecting (['ROOM']):
            self.expect ("ROOM")
            if self.integer ():
                self._curRoomNo = self._curInteger
                self._curRoom = newRoom (self._curRoomNo)
                if self._verbose:
                    print "roomDesc", curRoomNo
                while self.expecting (['DOOR', 'WALL', 'TREASURE', 'AMMO', 'WEAPON', 'LIGHT', 'MONSTER', 'SPAWN']):
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


def _runtests ():
    m = aas (os.path.join (os.path.join (os.environ['HOME'], ".local/share/dhewm3/base/maps"),
                           "tiny.pen"))

if __name__ == "__main__":
    _runtests ()
