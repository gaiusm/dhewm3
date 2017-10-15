#!/usr/bin/env python

import botlib, time

def walkSquare ():
    b.forward (100, 100)
    b.select (["move"])
    b.left (100, 100)
    b.select (["move"])
    b.back (100, 100)
    b.select (["move"])
    b.right (100, 100)
    b.select (["move"])


def runCircle (a):
    b.forward (100, 100)
    b.turn (a, 1)
    b.select (["move"])
    b.select (["turn"])


b = botlib.bot ("localhost", 'python_doommarine_1')
print "success!  python doom marine is alive"
print "trying to get my id...",
i = b.me ()
print "yes"
print "the python marine id is", i
print "the location of python marine is", b.getpos (i)
for i in range (1, b.maxobj ()+1):
    print "the location of python bot", i, "is", b.getpos (i)
while True:
    for a in range (0, 360, 45):
        # b.turn (a, 1)
        # b.select (["turn"])
        # walkSquare ()
        runCircle (a+180)
    time.sleep (5)
