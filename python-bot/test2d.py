#!/usr/bin/python

from array2d import array2d

a = array2d (20, 10, ' ')
print a.high ()


#
#  printf - keeps C programmers happy :-)
#

def printf (format, *args):
    print str(format) % args,


def dump ():
    for j in range (a.high ()[1]):
        s = ""
        for i in range (a.high ()[0]):
            s += a.get (i, j)
        printf ("%s\n", s)

y = a.high ()[1]-1
for i in range (a.high ()[0]):
    a.set (i, 0, '#')
    a.set (i, y, '#')

x = a.high ()[0]-1
for j in range (a.high ()[1]):
    a.set (0, j, '#')
    a.set (x, j, '#')

a.set (x/2, y/2, '#')
print len (a.get (x/2, y/2))

dump ()
