#!/usr/bin/env python

from __future__ import print_function
from __future__ import division

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
import fileinput
import sys

DONE = False

# ---

def debug(priority,*args):
  if ECHO > priority:
    print(*args,file=sys.stdout)

# ---

def read_line():
  global DONE

  while(True):
    line = input.readline()
    if not line:
      DONE = True
      return None
    line = line.strip()
    debug(4, "Read_line:", line)
    if line == '' or line[0] == '#': continue
    return line

# ---

def process_header():

    line = read_line()
    assert line, "Missing header"
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

      if LINE[0] in ('!','/','\\'):
        time_char = LINE[0]
        LINE = LINE[1:]
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

      draw_bells(LINE,beat,offset,y)

      LINE = read_line()

# ---

def draw_bells(line,beat,offset,y):

  if line == '-': return

  for bell in line.split(' '):

    if bell[0] == '*':
      page.setFont("Helvetica-Bold", CHAR_HEIGHT)
      bell = bell[1:]
    else:
      page.setFont("Helvetica", CHAR_HEIGHT)

    nbell = int(bell)
    assert FIRST <= nbell <= LAST, "Bell number bell outside declared range" 
    h_pos = H_MARGIN + (COLL_WIDTH*(beat+0.5)) +offset
    v_pos = LINE_HEIGHT*(LAST-nbell)
    page.drawCentredString(h_pos,v_pos,bell)
    debug(3, "    Plotting bell:", bell, "h_pos:", h_pos, "v_pos:", v_pos)

# ---

def process_page():
  global DONE

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

  page.showPage()
  DONE = True

# ---

# Echo: 0 - no output 1 - parameters 2 - info on each row
#       3 - info on each bell 4 - echo input

ECHO = 5

PAGESIZE=landscape(A4)
(WIDTH,HEIGHT) = PAGESIZE
debug(1, "Width:", WIDTH, "Height:", HEIGHT)
V_MARGIN = 0.5*inch
H_MARGIN = 0.5*inch
HEADER = 0.5*inch
SEPERATOR = 0.25*inch

PLAIN_LINE = 1
BAR_LINE = 2

PAGE_COUNTER = 1

input = fileinput.input()

(TITLE,BEATS,BARS,ROWS,FIRST,LAST) = process_header()
(TARGET_WIDTH, TARGET_HEIGHT, COLL_WIDTH, ROW_HEIGHT, 
  N_BELLS, CHAR_HEIGHT, LINE_HEIGHT) = setup_parameters()

source = input.filename()
target = source + ".pdf"
if source == '-': target = sys.stdout

page = canvas.Canvas(target, pagesize=PAGESIZE)

LINE = read_line()
assert not DONE, "Not even a beet of music"

while not DONE:
  process_page()

page.save()
