#!/usr/bin/env python3

import botbasic, time, sys, os
import botlib
from chvec import *
import math
import random

debugTowards = True
onefoot = 12  #  doom3 unit of measurement is one inch
gridUnit = 12 * 4 #  chisel unit is 4 feet



def sqr (x):
    return x * x

def calcDist (d0, d1):
    p0 = b.d2pv (d0)
    p1 = b.d2pv (d1)
    s = subVec (p0, p1)
    print ("p0 =", p0, "p1 =", p1, "s =", s)
    return math.sqrt (sqr (s[0]) + sqr (s[1]))


def is_close_doom3 (position1, position2):
    print ("is_close: ", end="")
    print (position1, position2)
    diff = subVec (position1, position2)
    hypot = math.sqrt (sqr (diff[0]) + sqr (diff[1]))
    print ("  result: ", hypot)
    return hypot <= gridUnit * 2


"""

    me_2d = b.d2pv (b.getpos (me))
    pos_2d = b.d2pv (b.getpos (i))
    b.turnface (subVec (pos_2d, me_2d))
    return b

"""

#
#  moveTowards - move bot towards object or label, i.
#

def moveTowards (b, i):
    b.reset ()
    print("will go and find", i)
    print("I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i))
    ### b.face_position (b.getpos (i))
    ### return b
    dest = b.d2pv (b.getpos (i))
    if debugTowards:
        print("bot is at", b.d2pv (b.getpos (me)))
        print("dest is at", dest)
    while not is_close_doom3 (b.getpos (me), b.getpos (i)):
        dest = b.d2pv (b.getpos (i))
        d = b.calcnav (i)
        if debugTowards:
            print("object", i, "is", d, "units away at pen coord", dest)
        if d is None:
            if debugTowards:
                print("cannot reach, randomly moving", i)
            # do something and move elsewhere
            b.turn (random.randint (-90, 90), 1)
            b.select (["turn"])
            b.forward (100, random.randint (8, 12))
            b.select (["move"])
            return b
        else:
            if debugTowards:
                print("distance according to dijkstra is", d)
            b.journey (100, d, b.d2pv (b.getpos (i)), i)
            if debugTowards:
                print("finished journey (...", i, ")")
                print("  result is that I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i))
                print("      penguin tower coords I'm at", b.d2pv (b.getpos (me)), "and", i, "is at", dest)
    # and face the object
    b.face (i)
    return b


def findAll (b):
    for i in b.allobj ():
        print("the location of python bot", me, "is", b.getpos (me))
        if i != me:
            b.aim (i)
            b = moveTowards (b, i)
            time.sleep (5)
    return b


def findYou (b):
    for i in b.allobj ():
        if i != b.me ():
            return i


def crouch_fire (b, you):
    b.reset ()
    b.face (you)
    b.changeWeapon (1)  # pistol
    b.face (you)
    # b.select (['move'])  # wait until bot has stopped moving
    b.startFiring ()
    b.crouch ()
    b.face (you)
    b.select (['move'])  # wait the crouch and fire single round to finish
    b.select (['fire'])
    b.stopFiring ()
    b.reloadWeapon ()


def combate (b, you):
    crouch_fire (b, you)


def calibrate ():
    b.reset ()
    b.forward (100, int (21 * gridUnit * .55))
    b.select (["move"])
    b.turn (270, 1)
    b.select (["turn"])
    b.forward (100, int (17 * gridUnit * .55))
    b.select (["move"])
    quit ()


def visit_label (b, label_list, visited_labels):
    visible_labels = []
    for label in label_list:
        b.reset ()  # is this necessary?
        label_entity_map = b._cache.getEntityNo ("label", label)
        label_entity_no = b._cache._basic.mapToRunTimeEntity (label_entity_map)
        if b.isvisible (label_entity_no):
            visible_labels += [[label, label_entity_no]]
        if not (label in visited_labels):
            visited_labels[label] = [[label, label_entity_no, 0]]
            print ("moving towards a label:", label)
            b = moveTowards (b, label_entity_no)
            return b, False, visited_labels
    return b, True, visited_labels

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

    print ("trying to get my id...", end=' ')
    me = b.me ()
    print ("yes")
    print ("the python marine id is", me)

    print("human player id is", end=' ')
    you = findYou (b)
    print (you)

    """
    while True:
        # calibrate ()
        b = moveTowards (b, you)
    """

    label_list = b.get_label_list ()  # obtains a list of label names from the pen map
    print ("bot has found these labels in the map:", label_list)
    while True:
        visited_labels = {}
        finished = False
        while not finished:
            # b, finished, visited_labels = visit_label (b, label_list, visited_labels)
            print ("moving towards you!")
            b = moveTowards (b, you)
            time.sleep (10)
            # combate (b, you)


if len (sys.argv) > 1:
    doommarine = int (sys.argv[1])

b = botlib.bot ("localhost", "python_doommarine %d" % (doommarine))
execBot (b, False)
