#!/usr/bin/env python

import botbasic, time
import botlib

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


def testturn (a):
    b.turn (a, 1)
    b.select (["turn"])


def moveTowards (i):
    b.reset ()
    print "will go and find", i
    print "I'm currently at", b.getpos (me), "and", i, "is at", b.getpos (i)
    d = b.calcnav (i)
    print "object", i, "is", d, "units away"
    b.journey (100, d, b.getpos (i))
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


b = botlib.bot ("localhost", 'python_doommarine_1')
# b = botbasic.basic ("localhost", 'python_doommarine_1')
print "success!  python doom marine is alive"
print "trying to get my id...",
me = b.me ()
print "yes"
print "the python marine id is", me
print "the location of python marine is", b.getpos (me)
while True:
    # circle ()
    testturn (0)
    time.sleep (3)
    testturn (90)
    time.sleep (3)
    testturn (180)
    time.sleep (3)
    testturn (270)
    time.sleep (3)
    testturn (270)
    time.sleep (3)
    testturn (270)
    time.sleep (3)
    testturn (270)
    time.sleep (3)


    """
    for i in b.allobj ():
        if i != me:
            print "the location of python bot", me, "is", b.getpos (me)
            b.face (i)
            time.sleep (5)
    """
