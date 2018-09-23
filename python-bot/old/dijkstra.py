#!/usr/bin/python

import string


infinity = 1000000


#
#  error - issues a syntax error
#

def error (message):
    print "%s" % (message)


class node:
    global infinity

    name = ""
    neighbours = {}        #  dictionary of names of neighbours and their relative cost from us
    previous = 'undefined' #  where have we come from?
    distance = infinity    #  the absolute distance from source
    def __init__ (self, n):
        self.name = n
        self.neighbours = {}
        self.previous = 'undefined'
        self.distance = infinity
    def reset (self):
        self.previous = 'undefined'
        self.distance = infinity
    def update (self, prev, dist):
        self.previous = prev
        self.distance = dist
    def getDistanceFrom (self, n):
        if n == self.name:
            return 0
        else:
            return self.distance
    def getPrevious (self):
        return self.previous
    def getName (self):
        return self.name
    def addLength (self, toNode, length):
        if self.neighbours.has_key (toNode):
            error (self.name + " already knows about node: " + toNode)
        else:
            self.neighbours[toNode] = length
    def getLength (self, toNode):
        if self.neighbours.has_key (toNode):
            return self.neighbours[toNode]
        else:
            error (self.name + " does not know about node: " + toNode)
    def getNeighbours(self):
        l = []
        for i, j in self.neighbours.iteritems ():
            l += [i]
        return l

class graph:
    nodes = []
    choices = []
    consider = "unknown"
    visited = []
    def __init__ (self):
        self.nodes = []
        self.choices = []
        self.consider = "unknown"
        self.visited = []
    def reset (self, source):
        self.choices = [source]
        self.visited = []
        self.getNode (source).update(source, 0)
    def setConsider (self, n):
        self.consider = n
    def getChoices (self):
        return self.choices
    def addChoice (self, n):
        if (not (n in self.visited)) and (not (n in self.choices)):
            print "adding node", n, "to choice list"
            self.choices += [n]
    def addVisited (self, n):
        self.visited += [n]
    def getVisited (self):
        return self.visited
    def getNode (self, n):
        for i in self.nodes:
            if n == i.getName ():
                return i
        else:
            error ("cannot find node " + n + " in graph")
    def addLength (self, source, dest, length):
        for i in self.nodes:
            if source == i.getName():
                i.addLength(dest, length)
        else:
            self.nodes += [node(source)]
            self.nodes[-1].addLength(dest, length)
    def getLength (self, u, v):
        for i in self.nodes:
            if u == i.getName ():
                return i.getLength (v)
        else:
            error ("cannot find node " + u + " in graph")
    def getBestChoice (self, source):
        # returns the node which has the shortest distance from the source
        i = 0
        bi = 0
        best = self.choices[0]
        for c in self.choices[1:]:
            i += 1
            if theGraph.getNode (c).getDistanceFrom (source) < theGraph.getNode (best).getDistanceFrom (source):
                best = c
                bi = i
        del self.choices[bi]
        print "the best choice was", best, "with a cost of", theGraph.getNode (best).getDistanceFrom (source)
        return best


#
#  findRoute - dijkstra's algorithm.
#

def findRoute (source, dest):
    global theGraph

    theGraph.reset (source)
    while theGraph.getChoices() != []:
        print "we have the following nodes to explore:", theGraph.getChoices()
        u = theGraph.getBestChoice(source)
        print "have chosen", u
        print "visited the following:", theGraph.getVisited()
        theGraph.addVisited(u)
        print "node", u, "has neighbours", theGraph.getNode(u).getNeighbours()
        if u == dest:
            print "found route, finishing"
            return True
        for v in theGraph.getNode(u).getNeighbours():
            theGraph.addChoice(v)
            alt = theGraph.getNode(u).getDistanceFrom(source) + theGraph.getLength(u, v)
            if alt < theGraph.getNode(v).getDistanceFrom(source):
                print "found a better route to '", v, "' value", alt, "from '", source, "'",
                print " the previous value was", theGraph.getNode(v).getDistanceFrom(source)
                theGraph.getNode(v).update(u, alt)
    print "cannot find route between", source, "and", dest
    return False


#
#  displayRoute -
#

def displayRoute(source, dest):
    global theGraph

    print "the route from", source, "to", dest
    route = [dest]
    while dest != source:
        print dest
        dest = theGraph.getNode(dest).getPrevious()
        route = [dest] + route
    print route
    total = 0
    if len(route)>1:
        p = route[0]
        print "initially start at node '", p, "'"
        for i in route[1:]:
            total += theGraph.getNode(i).getLength(p)
            print "go to '", i, "' a distance of", theGraph.getNode(i).getLength(p), " running total", total
            p = i

#
#  processLine - adds nodes to the graph, and in so doing it
#                creates a graph.  It also reads in the routing
#                questions and calls a function to solve them.
#

def processLine(line):
    global theGraph

    print line
    uncomment = string.split(line, '#')
    words = string.split(string.lstrip(uncomment[0]))
    if len(words)>=2:
        f=words[0]
        if f == "find":
            if (len(words) == 4) and (words[2] == "->"):
                if findRoute(words[1], words[3]):
                    displayRoute(words[1], words[3])
            else:
                syntaxError("expecting 'from source -> dest'")
        else:
            for word in words[1:]:
                t = string.split(word, ':')
                if len(t) == 2:
                    theGraph.addLength(f, t[0], int(t[1]))
                else:
                    syntaxError("expecting node:distance entity")

theGraph = graph()

#
#  main - calls scanner with a filename and a function to process each
#         line of the file.
#

def main():
    scanner("simplea.data", processLine)

main()
