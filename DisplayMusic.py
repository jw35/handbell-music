#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import inch
import fileinput
import sys
import re
import os

DONE = False

# ---

def debug(priority,*args):
  if ECHO > priority:
    print(*args,file=sys.stderr)

# ---

def group(l):
    first = last = l[0]
    for n in l[1:]:
        if n - 1 == last: # Part of the group, bump the end
            last = n
        else: # Not part of the group, yield current group and start a new
            yield first, last
            first = last = n
    yield first, last # Yield the last group

# ---

def analyse_bells(bells):

    # Seperate bells in the main scale from the accidentals
    mainscale = []
    accidentals = []
    for bell in bells:
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

# ---

def read_line():
  global DONE

  while(True):
    line = input.readline()
    if not line:
      debug(4, "End of file")
      DONE = True
      return None
    line = line.strip()
    debug(4, "Read_line:", line)
    if line == '' or line[0] == '#': continue
    return line

# ---

def process_header():

    line = read_line()
    assert line, "Missing title"
    TITLE = line.strip()
    debug(0, "Title:", TITLE)

    line = read_line()
    assert line, "Missing parameters"
    (BEATS,BARS,ROWS,FIRST,LAST) = (int(x) for x in line.strip().split())
    debug(0, "Beets per bar:", BEATS)
    debug(0, "Bars per line:", BARS)
    debug(0, "Lines per page:", ROWS)
    debug(0, "Bells from:", FIRST, "to:", LAST)

    return (TITLE,BEATS,BARS,ROWS,FIRST,LAST)

# ---

def setup_parameters():

    TARGET_WIDTH = WIDTH-(2*H_MARGIN)
    TARGET_HEIGHT = HEIGHT-(2*V_MARGIN)-HEADER
    debug(1, "Target width:", TARGET_WIDTH, "Target height:", TARGET_HEIGHT)

    COLL_WIDTH = TARGET_WIDTH/(BARS*BEATS)
    debug(1, "Collumn width:", COLL_WIDTH)

    ROW_HEIGHT = (TARGET_HEIGHT - (SEPERATOR*(ROWS-1)))/ROWS
    debug(1, "Row height:", ROW_HEIGHT)

    N_BELLS = LAST - FIRST + 1
    debug(1, "Number of bells:", N_BELLS)
    CHAR_HEIGHT = 0.8 * COLL_WIDTH
    LINE_HEIGHT = (ROW_HEIGHT - CHAR_HEIGHT - 5) / ((N_BELLS-1)/2)
    if CHAR_HEIGHT > LINE_HEIGHT: CHAR_HEIGHT = LINE_HEIGHT 
    debug(1, "Character height:", CHAR_HEIGHT, "Line height:", LINE_HEIGHT)

    return(TARGET_WIDTH, TARGET_HEIGHT, COLL_WIDTH, ROW_HEIGHT, N_BELLS, CHAR_HEIGHT, LINE_HEIGHT)

# ---


def process_row(y):
    global DONE, LINE

    page.setLineWidth(BAR_LINE)
    page.rect(H_MARGIN, y, TARGET_WIDTH, ROW_HEIGHT)
    for beat in range(1,BARS*BEATS):
      #debug(2, beat, BEATS, PLANE_LINE, BAR_LINE)
      page.setLineWidth(BAR_LINE if beat % BEATS == 0 else PLAIN_LINE)
      debug(2, "Beet x:", H_MARGIN+(beat*COLL_WIDTH), "Beet y:", y)
      page.line(H_MARGIN+(beat*COLL_WIDTH), y, H_MARGIN+(beat*COLL_WIDTH), y+ROW_HEIGHT)

    beat = 0
    while not DONE:

      line = LINE
      if line[0] in ('!','/','\\'):
        time_char = line[0]
        line = line[1:]
      else:
        time_char = ''

      if time_char == '!':
        offset = COLL_WIDTH/2
        debug(2,"Half beet")
      elif time_char == '/':
        beat += 1
        offset = -COLL_WIDTH/5
        debug(2,"Double beat, part 1")
      elif time_char == '\\':
        offset = COLL_WIDTH/5
        debug(2,"Double beat, part 2")
      else:
        beat += 1
        offset = 0
        debug(2,"Full beat")

      # have we gone off the current row?

      debug(2, "Current beat:", beat, "offset:", offset)
      if beat > (BEATS*BARS): break

      draw_bells(line,beat,offset,y)

      LINE = read_line()

# ---

def draw_bells(line,beat,offset,y):

  if line == '-': return

  for bell in line.split():

    if bell[0] == '*':
      page.setFont("Helvetica-Bold", CHAR_HEIGHT)
      bell = bell[1:]
    else:
      page.setFont("Helvetica", CHAR_HEIGHT)

    debug(3, "Plotting bell", bell)
    BELLS_USED.add(bell) 
    nbell = int(re.sub(r'[^\d]','',bell))
    assert FIRST <= nbell <= LAST, "Bell number bell outside declared range" 
    h_pos = H_MARGIN + (COLL_WIDTH*(beat-0.5)) + offset
    v_pos = y+(LINE_HEIGHT*(LAST-nbell+0.5)/2)
    page.drawCentredString(h_pos,v_pos,bell)
    debug(3, "    Plotting bell:", bell, "h_pos:", h_pos, "v_pos:", v_pos)

# ---

def process_page():
  global DONE, PAGE_COUNTER

  page.setFont("Helvetica-Bold", 30)

  t = "%s (page %d)" % (TITLE, PAGE_COUNTER)
  if PAGE_COUNTER == 1: t = TITLE
  page.drawCentredString(WIDTH/2, V_MARGIN+TARGET_HEIGHT+0.5*HEADER, t)
  
  page.setFont("Helvetica", CHAR_HEIGHT)

  # E.g. 2,1,0 for ROWS=3
  for row in range(ROWS-1,-1,-1):

    y = V_MARGIN + (row*(ROW_HEIGHT+SEPERATOR))

    process_row(y)
    if DONE: break

  t = analyse_bells(BELLS_USED)
  page.setFont("Helvetica", 15)
  page.drawRightString(WIDTH-H_MARGIN, V_MARGIN+TARGET_HEIGHT+0.5*HEADER, t)

  PAGE_COUNTER += 1
  page.showPage()

# ---

# Echo: 0 - no output 1 - parameters 2 - info on each row
#       3 - info on each bell 4 - echo input

ECHO = 0

PAGESIZE=landscape(A3)
(WIDTH,HEIGHT) = PAGESIZE
debug(1, "Width:", WIDTH, "Height:", HEIGHT)
V_MARGIN = 0.5*inch
H_MARGIN = 0.6*inch
HEADER = 0.5*inch
SEPERATOR = 0.25*inch

PLAIN_LINE = 1
BAR_LINE = 2

PAGE_COUNTER = 1
BELLS_USED = set()

input = fileinput.input()

(TITLE,BEATS,BARS,ROWS,FIRST,LAST) = process_header()
(TARGET_WIDTH, TARGET_HEIGHT, COLL_WIDTH, ROW_HEIGHT, 
  N_BELLS, CHAR_HEIGHT, LINE_HEIGHT) = setup_parameters()

source = input.filename()
if source == '<stdin>':
  target = sys.stdout
else:
  base = os.path.splitext(source)[0]
  target = base + ".pdf"

page = canvas.Canvas(target, pagesize=PAGESIZE)

LINE = read_line()
assert not DONE, "Not even a beet of music"

while not DONE:
  process_page()

page.save()
