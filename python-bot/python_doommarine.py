#!/usr/bin/env python3

import botbasic, time, sys, os
import botlib
from chvec import *
import math

debugTowards = False


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
            print("attempting to change to weapon", w, end=' ')
            print("dhewm3 returns", b.changeWeapon (w))
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

#
#  moveTowards - move towards object, i.
#

def moveTowards (i):
    b.reset ()
    print("will go and find", i)
    print("I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i))
    """
    if not equVec (b.d2pv (b.getpos (me)), [12, 9]):
        print "failed to find getpos at 12, 9 for python"
    if not equVec (b.d2pv (b.getpos (i)), [40, 3]):
        print "failed to find getpos at 40, 3 for player"
    """
    if debugTowards:
        print("bot is at", b.d2pv (b.getpos (me)))
        print("you are at", b.d2pv (b.getpos (you)))
    d = b.calcnav (i)
    if debugTowards:
        print("object", i, "is", d, "units away")
    if d is None:
        if debugTowards:
            print("cannot reach", i)
        b.turn (90, 1)
        b.select (["turn"])
        b.forward (100, 100)
        b.select (["move"])
    else:
        if debugTowards:
            print("distance according to dijkstra is", d)
        b.journey (100, d, i)
        if debugTowards:
            print("finished my journey to", i)
            print("  result is that I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i))
            print("      penguin tower coords I'm at", b.d2pv (b.getpos (me)), "and", i, "is at", b.d2pv (b.getpos (i)))


#
#  move_towards - move bot, b, towards position, pos.
#                 pos is penguin tower coordinates.
#

def move_towards (b, pos, velocity):
    b.reset ()
    dist = b.calcnav_pos (pos)
    if dist is None:
        if debugTowards:
           print("cannot reach", pos)
        b.turn (90, 1)
        b.select (["turn"])
        b.forward (velocity, velocity)
        b.select (["move"])
    else:
        if debugTowards:
            print("distance according to dijkstra is", dist)
        b.journey_pos (velocity, dist, pos)
        if debugTowards:
            print("finished my journey to", pos)
            print("  I'm at", b.d2pv (b.getpos (me)))


def findAll ():
    for i in b.allobj ():
        print("the location of python bot", me, "is", b.getpos (me))
        if i != me:
            b.aim (i)
            moveTowards (i)
            time.sleep (5)

def findYou (b):
    for i in b.allobj ():
        if i != b.me ():
            return i


def antiClock (b):
    print("finished west, north, east, south")
    print("west, north, east, south diagonal")
    for v in [[1, 1], [-1, 1], [-1, -1], [1, -1]]:
        print("turning", end=' ')
        b.turnface (v, 1)
        b.sync ()
        print("waiting")
        time.sleep (10)
        print("next")
        b.reset ()


def clock (b):
    print("finished west, north, east, south")
    print("west, north, east, south diagonal")
    for v in [[1, 1], [1, -1], [-1, -1], [-1, 1]]:
        print("turning", end=' ')
        b.turnface (v, -1)
        b.sync ()
        print("waiting")
        time.sleep (10)
        print("next")
        b.reset ()

#
#  test_crouch - make the bot crouch and then jump.
#

def test_crouch_jump (b):
    b.reset ()
    b.stepup (-2, 3*12)
    b.select (['move'])
    # time.sleep (2)
    b.stepup (100, 4*12)
    b.select (['move'])


def crouch_fire (b, you):
    b.reset ()
    b.face (you)
    b.change_weapon (1)  # pistol
    b.face (you)
    # b.select (['move'])  # wait until bot has stopped moving
    b.start_firing ()
    b.stepup (-2, 4*12)  # crouch
    b.face (you)
    b.select (['move'])  # wait the crouch and fire single round to finish
    b.select (['fire'])
    b.stop_firing ()
    b.reload_weapon ()


#
#
#

def guard_sentry (b):
    me = b.me ()
    you = findYou (b)
    start_pos = b.d2pv (b.getpos (me))  # penguin tower coords
    end_pos = addVec (start_pos, [10, 0])  # penguin tower coords
    while True:
        move_towards (b, end_pos, 100)
        b.turn (180, 1)
        b.select (["turn"])
        crouch_fire (b, you)
        time.sleep (1)  # --fixme-- should check for activity!
        move_towards (b, start_pos, 100)
        b.turn (180, 1)
        b.select (["turn"])
        crouch_fire (b, you)
        time.sleep (1)  # --fixme-- should check for activity!

doommarine = -2

def execBot (b, useExceptions = True):
    if useExceptions:
        try:
            botMain (b)
        except:
            print("bot was killed, or script terminated")
            return
    else:
        botMain (b)


def botMain (b):
    global me
    print("success!  python doom marine is alive")

    print("trying to get my id...", end=' ')
    me = b.me ()
    print("yes")
    print("the python marine id is", me)

    pos = b.getpos (me)
    pen = b.d2pv (pos)
    print ("pos = ", pos, "pen coords =", pen)
    # sys.exit (0)

    while True:
        findAll ()
        # guard_sentry (b)


if len (sys.argv) > 1:
    doommarine = int (sys.argv[1])

b = botlib.bot ("localhost", "python_doommarine %d" % (doommarine))
execBot (b, False)
