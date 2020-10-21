#!/usr/bin/env python3

import botbasic, time, sys, os
import botlib
from chvec import *
import math
import random

debugTowards = True


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print(str(format) % args, end=' ')


def walkSquare ():
    bot.forward (100, 100)
    bot.select (["move"])
    bot.left (100, 100)
    bot.select (["move"])
    bot.back (100, 100)
    bot.select (["move"])
    bot.right (100, 100)
    bot.select (["move"])


def runArc (a):
    bot.forward (100, 100)
    bot.turn (a, 1)
    bot.select (["move"])
    bot.select (["turn"])


def circle ():
    while True:
        for a in range (0, 360, 45):
            runArc (a+180)
        time.sleep (5)
        for w in range (0, 10):
            print("attempting to change to weapon", w, end=' ')
            print("dhewm3 returns", bot.changeWeapon (w))
            time.sleep (3)

def testturn (a):
    bot.turn (a, 1)
    bot.select (["turn"])

def sqr (x):
    return x * x

def calcDist (d0, d1):
    p0 = bot.d2pv (d0)
    p1 = bot.d2pv (d1)
    s = subVec (p0, p1)
    return math.sqrt (sqr (s[0]) + sqr (s[1]))

#
#  moveTowards - move towards object, i.
#

def moveTowards (i):
    bot.reset ()
    print("will go and find", i)
    print("I'm currently at", bot.getpos (me), "and", i, "is at", bot.getpos (i))
    """
    if not equVec (bot.d2pv (bot.getpos (me)), [12, 9]):
        print "failed to find getpos at 12, 9 for python"
    if not equVec (bot.d2pv (bot.getpos (i)), [40, 3]):
        print "failed to find getpos at 40, 3 for player"
    """
    if debugTowards:
        print("bot is at", bot.d2pv (bot.getpos (me)))
        print("you are at", bot.d2pv (bot.getpos (i)))
    d = bot.calcnav (i)
    if debugTowards:
        print("object", i, "is", d, "units away")
    if d is None:
        if debugTowards:
            print("cannot reach", i)
        bot.turn (90, 1)
        bot.select (["turn"])
        bot.forward (100, 10)
        bot.select (["move"])
    else:
        if debugTowards:
            print("distance according to dijkstra is", d)
        bot.journey (100, d, i)
        if debugTowards:
            print("finished my journey to", i)
            print("  result is that I'm currently at", bot.getpos (me), "and", i, "is at", bot.getpos (i))
            print("      penguin tower coords I'm at", bot.d2pv (bot.getpos (me)), "and", i, "is at", bot.d2pv (bot.getpos (i)))


#
#  move_towards - move bot towards position, pos.
#                 pos is penguin tower coordinates.
#

def move_towards (pos, velocity):
    bot.reset ()
    dist = bot.calcnav_pos (pos)
    if dist is None:
        if debugTowards:
            print ("cannot reach", pos, "bot moving randomly")
        bot.turn (random.randint (-90, 90), 1)
        bot.select (["turn"])
        bot.forward (velocity, velocity)
        bot.select (["move"])
    else:
        if debugTowards:
            print("distance according to dijkstra is", dist)
        bot.journey_pos (velocity, dist, pos)
        if debugTowards:
            print("finished my journey to", pos)
            print("  I'm at", bot.d2pv (bot.getpos (me)))


def findAll ():
    for i in bot.allobj ():
        print("the location of python bot", me, "is", bot.getpos (me))
        if i != me:
            bot.aim (i)
            moveTowards (i)
            time.sleep (5)

def findYou ():
    for i in bot.allobj ():
        if i != bot.me ():
            return i


def antiClock ():
    print("finished west, north, east, south")
    print("west, north, east, south diagonal")
    for v in [[1, 1], [-1, 1], [-1, -1], [1, -1]]:
        print("turning", end=' ')
        bot.turnface (v, 1)
        bot.sync ()
        print("waiting")
        time.sleep (10)
        print("next")
        bot.reset ()


def clock ():
    print("finished west, north, east, south")
    print("west, north, east, south diagonal")
    for v in [[1, 1], [1, -1], [-1, -1], [-1, 1]]:
        print("turning", end=' ')
        bot.turnface (v, -1)
        bot.sync ()
        print("waiting")
        time.sleep (10)
        print("next")
        bot.reset ()

#
#  test_crouch - make the bot crouch and then jump.
#

def test_crouch_jump ():
    bot.reset ()
    bot.stepup (-2, 3*12)
    bot.select (['move'])
    # time.sleep (2)
    bot.stepup (100, 4*12)
    bot.select (['move'])


def crouch_fire (you):
    bot.reset ()
    bot.face (you)
    bot.change_weapon (1)  # pistol
    bot.face (you)
    # bot.select (['move'])  # wait until bot has stopped moving
    bot.start_firing ()
    bot.stepup (-2, 4*12)  # crouch
    bot.face (you)
    bot.select (['move'])  # wait the crouch and fire single round to finish
    bot.select (['fire'])
    bot.stop_firing ()
    bot.reload_weapon ()


#
#
#

def guard_sentry ():
    me = bot.me ()
    you = findYou ()
    start_pos = bot.d2pv (bot.getpos (me))  # penguin tower coords
    end_pos = addVec (start_pos, [10, 0])  # penguin tower coords
    while True:
        move_towards (end_pos, 100)
        bot.turn (180, 1)
        bot.select (["turn"])
        crouch_fire (you)
        time.sleep (1)  # --fixme-- should check for activity!
        move_towards (start_pos, 100)
        bot.turn (180, 1)
        bot.select (["turn"])
        crouch_fire (you)
        time.sleep (1)  # --fixme-- should check for activity!


def testVisibility (disappear, disappear_head, water, materialise, materialise_head):
    bot.setvisibilityshader (disappear)  # all players entities use disappear
    bot.setvisibilityshader (disappear_head, ["player2_head"])  #  change the head entity
    bot.visibilityParams ([8])   # run visibility effects for a duration of 8 seconds
    bot.visibilityFlag (True)    # turn on the visibility flag for all player entities.
    bot.flipVisibility ()        # now release all the above info to the renderer
    bot.face (1)                 # turn and face player 1 (human)
    time.sleep (7)             # wait for 7 seconds
    bot.face (1)                 # turn and face player 1 (human)
    bot.setvisibilityshader (water)
    bot.visibilityFlag (True)
    bot.visibilityParams ([3, 3])
    bot.flipVisibility ()        # now release all the above info to the renderer
    bot.face (1)                 # turn and face player 1 (human)
    time.sleep (6)             # wait for 6 seconds
    bot.setvisibilityshader (water)
    bot.visibilityFlag (True)
    bot.visibilityParams ([3, 3])
    bot.flipVisibility ()
    bot.setvisibilityshader (materialise)
    bot.setvisibilityshader (materialise_head, ["player2_head"])
    bot.visibilityParams ([14])
    bot.visibilityFlag (True)
    bot.flipVisibility ()        # now release all the above info to the renderer
    bot.face (1)                 # turn and face player 1 (human)
    time.sleep (14)            # wait for 14 seconds
    bot.visibilityFlag (False)
    bot.flipVisibility ()
    time.sleep (3)             # wait for 3 seconds


#
#  visibilityExamples - some test examples to stress the visibility API.
#

def visibilityExamples ():
    testVisibility ("melt/model/player/green/body2inv",
                    "melt/model/player/green/head2inv",
                    "pulse/melt/model/player",
                    "melt/model/player/green/inv2body",
                    "melt/model/player/green/inv2head")
    # testVisibility ("melt")  # works
    # testVisibility ("melt/model/player", "visibility")
    # testVisibility ("melt/models/characters/player/body2")
    # testVisibility ("visibility")
    # testVisibility ("textures/stone/sand01")


def execBot (useExceptions = True):
    if useExceptions:
        try:
            botMain ()
        except:
            print ("bot was killed, or script terminated")
            return
    else:
        botMain ()


def botMain ():
    global me
    print ("success!  python doom marine is alive")

    printf ("trying to get my id...")
    me = bot.me ()
    printf ("yes\n")
    printf ("the python marine id is: %d\n", me)

    pos = bot.getpos (me)
    pen = bot.d2pv (pos)
    print ("pos = ", pos, "pen coords =", pen)
    print ("getselfentitynames =", bot.getselfentitynames ())
    while True:
        visibilityExamples ()
        # guard_sentry ()
        # findAll ()


doommarine = -2  # default unset value - which will yield an
                 # error if sent up to the server

if len (sys.argv) > 1:
    doommarine = int (sys.argv[1])

#
#  much safer when developing to keep bot global to
#  ensure a single global bot is created.
#
bot = botlib.bot ("localhost", "python_doommarine %d" % (doommarine))
execBot (False)
