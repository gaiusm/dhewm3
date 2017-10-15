#!/usr/bin/env python

import botlib, time

b = botlib.bot ("localhost", 'python_doommarine_2')
print "success!  python second doom marine is alive"
print "trying to get my id",
i = b.me ()
print "yes..."
print "the python marine id is", i
print "the location of python marine is", b.getpos (i)
for i in range (1, b.maxobj ()+1):
    print "the location of python bot", i, "is", b.getpos (i)
while True:
    for a in range (0, 360, 30):
        b.turn (a)
        time.sleep (3)
    time.sleep (5)
    b.right (100, 100)
    time.sleep (5)
    b.forward (100, 100)
    time.sleep (5)
    b.left (100, 100)
    time.sleep (5)
    b.back (100, 100)
    time.sleep (5)
    b.stepvec (100, 100, 10)
    time.sleep (5)
    b.stepvec (-100, 100, 10)
    time.sleep (5)

    """
    for j in range (1, b.maxobj ()+1):
        time.sleep (5)
        if i != j:
            print "aiming at", j
            print b.aim (j)
            time.sleep (1)
            # print "fire at", j
            print b.start_firing ()
            time.sleep (3)
            print b.stop_firing ()
            time.sleep (1)
            print b.reload_weapon ()
    """
