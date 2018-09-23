#!/usr/bin/env python

import botbasic, time
import botlib
from chvec import *
import math

def walkSquare ():
    b.forward (100, 100)
    b.select (["move"])
    b.left (100, 100)
    b.select (["move"])
    b.back (100, 100)
    b.select (["move"])
    b.right (100, 100)
    b.select (["move"])


def runArc (a):
    b.forward (100, 100)
    b.turn (a, 1)
    b.select (["move"])
    b.select (["turn"])


def circle ():
    while True:
        for a in range (0, 360, 45):
            runArc (a+180)
        time.sleep (5)
        for w in range (0, 10):
            print "attempting to change to weapon", w,
            print "dhewm3 returns", b.changeWeapon (w)
            time.sleep (3)

def testturn (a):
    b.turn (a, 1)
    b.select (["turn"])

def sqr (x):
    return x * x

def calcDist (d0, d1):
    p0 = b.d2pv (d0)
    p1 = b.d2pv (d1)
    s = subVec (p0, p1)
    return math.sqrt (sqr (s[0]) + sqr (s[1]))

def moveTowards (i):
    b.reset ()
    print "will go and find", i
    print "I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i)
    if not equVec (b.d2pv (b.getpos (me)), [12, 9]):
        print "failed to find getpos at 12, 9 for python"
    if not equVec (b.d2pv (b.getpos (i)), [40, 3]):
        print "failed to find getpos at 40, 3 for player"
    print "bot is at", b.d2pv (b.getpos (me))
    print "you are at", b.d2pv (b.getpos (you))
    d = b.calcnav (i)
    print "object", i, "is", d, "units away"
    if d is None:
        print "cannot reach", i
        b.turn (90, 1)
        b.select (["turn"])
        b.forward (100, 100)
        b.select (["move"])
    else:
        print "distance according to dijkstra is", d
        b.journey (100, d, i)
        print "finished my journey to", i
        print "  result is that I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i)
        print "      penguin tower coords I'm at", b.d2pv (b.getpos (me)), "and", i, "is at", b.d2pv (b.getpos (i))


def findAll ():
    for i in b.allobj ():
        print "the location of python bot", me, "is", b.getpos (me)
        if i != me:
            b.aim (i)
            moveTowards (i)
            time.sleep (5)

def findYou (b):
    for i in b.allobj ():
        if i != b.me ():
            return i


def antiClock (b):
    print "finished west, north, east, south"
    print "west, north, east, south diagonal"
    for v in [[1, 1], [-1, 1], [-1, -1], [1, -1]]:
        print "turning",
        b.turnface (v, 1)
        b.sync ()
        print "waiting"
        time.sleep (10)
        print "next"
        b.reset ()


def clock (b):
    print "finished west, north, east, south"
    print "west, north, east, south diagonal"
    for v in [[1, 1], [1, -1], [-1, -1], [-1, 1]]:
        print "turning",
        b.turnface (v, -1)
        b.sync ()
        print "waiting"
        time.sleep (10)
        print "next"
        b.reset ()

#def face (b):
#    b.reset ()
#    print "your pen location is", b.d2pv (b.getpos (you))
#    print "my pen position is", b.d2pv (b.getpos (me))
#
#    v = subVec (b.d2pv (b.getpos (you)), b.d2pv (b.getpos (me)))
#    b.turnface (v)
#    b.sync ()
#    print "using method 2"
#    b.aim (you)
#    b.reset ()


b = botlib.bot ("localhost", 'python_doommarine_1')
# b = botbasic.basic ("localhost", 'python_doommarine_1')
print "success!  python doom marine is alive"

print "trying to get my id...",
me = b.me ()
print "yes"
print "the python marine id is", me
you = findYou (b)

while True:
    moveTowards (you)
    b.face (you)
    # b.fire ()
    time.sleep (3)
