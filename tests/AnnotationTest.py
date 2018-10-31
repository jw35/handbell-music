#!/usr/bin/env python

from __future__ import print_function
import re

def group(l):
    first = last = l[0]
    for n in l[1:]:
        if n - 1 == last: # Part of the group, bump the end
            last = n
        else: # Not part of the group, yield current group and start a new
            yield first, last
            first = last = n
    yield first, last # Yield the last group

def analyse_bells(bells):

    # Seperate bells in the main scale from the accidentals
    mainscale = []
    accidentals = []
    for bell in test:
	   match = re.match(r'^(\d*)$', bell)
	   if match:
	       mainscale.append(int(match.group(1)))
	   else:
	       accidentals.append(bell)

    # group and format the main scale bells
    tgroups = []
    for g in group(sorted(mainscale)):
        if g[0] == g[1]: # group with one member
            tgroups.append("%d" % (g[0]))
        elif g[0] + 1 == g[1]: # group with two members
            tgroups.append("%d" % (g[0]))
            tgroups.append("%d" % (g[1]))
        else: # longer group
            tgroups.append("%s-%s" % (g[0],g[1]))

    # format the accidentals
    atext = ''
    if accidentals:
        atext = ' + ' + ", ".join(sorted(accidentals))

    return ', '.join(tgroups) + atext



test = {'3', '2', '1', '4', '5', '7', '7#', '8', '9#', '10', '12'}

print(analyse_bells(test))