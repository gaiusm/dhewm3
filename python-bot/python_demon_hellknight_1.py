#!/usr/bin/env python

import botlib, time

b = botlib.bot ("localhost", 'python_demon_hellknight_1')
print "success!  python is alive"
i = b.me ()
print "the python bot id is", i
print "the location of python bot is", b.getpos (i)
for i in range (1, b.maxobj ()+1):
    print "the location of python bot", i, "is", b.getpos (i)
while True:
    for d in range (64):
        print b.step (float (d)/10.0)
        time.sleep (1)
