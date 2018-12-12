#!/usr/bin/env python3

from __future__ import print_function
from __future__ import division

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, portrait
from reportlab.lib.units import inch
import fileinput
import sys
import re
import os
import platform
import datetime

DONE = False

# ---


def debug(priority, *args):
    if ECHO > priority:
        print(*args, file=sys.stderr)

# ---


def group(l):
    first = last = l[0]
    for n in l[1:]:
        if n - 1 == last:  # Part of the group, bump the end
            last = n
        else:  # Not part of the group, yield current group and start a new
            yield first, last
            first = last = n
    yield first, last  # Yield the last group

# ---


def analyse_bells(bells):

    # Seperate bells in the main scale from the accidentals
    mainscale = set()
    accidentals = set()
    for bell in bells:
        bell = re.sub(r'\((.*)\)', r'\1', bell)
        match = re.match(r'^(\d*)$', bell)
        if match:
            mainscale.add(int(match.group(1)))
        else:
            accidentals.add(bell)

    # group and format the main scale bells
    tgroups = []
    for g in group(sorted(mainscale)):
        if g[0] == g[1]:  # group with one member
            tgroups.append("%d" % (g[0]))
        elif g[0] + 1 == g[1]:  # group with two members
            tgroups.append("%d" % (g[0]))
            tgroups.append("%d" % (g[1]))
        else:  # longer group
            tgroups.append("%s-%s" % (g[0], g[1]))

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
        if line == '' or line[0] == '#':
            continue
        return line

# ---


def process_header():

    line = read_line()
    assert line, "Missing title"
    TITLE = line.strip()
    debug(0, "Title:", TITLE)

    line = read_line()
    assert line, "Missing parameters"
    (BEATS, BARS, ROWS, FIRST, LAST) = (int(x) for x in line.strip().split())
    debug(0, "Beets per bar:", BEATS)
    debug(0, "Bars per line:", BARS)
    debug(0, "Lines per page:", ROWS)
    debug(0, "Bells from:", FIRST, "to:", LAST)

    return (TITLE, BEATS, BARS, ROWS, FIRST, LAST)

# ---


def setup_parameters():

    TARGET_WIDTH = WIDTH-(2*H_MARGIN)
    TARGET_HEIGHT = HEIGHT-TOP_MARGIN-BOTTOM_MARGIN-HEADER
    debug(1, "Target width:", TARGET_WIDTH, "Target height:", TARGET_HEIGHT)

    COLL_WIDTH = TARGET_WIDTH/(BARS*BEATS)
    debug(1, "Collumn width:", COLL_WIDTH)

    ROW_HEIGHT = (TARGET_HEIGHT - (SEPERATOR*(ROWS-1)))/ROWS
    debug(1, "Row height:", ROW_HEIGHT)

    N_BELLS = LAST - FIRST + 1
    debug(1, "Number of bells:", N_BELLS)

    LINE_HEIGHT = ROW_HEIGHT/(N_BELLS+0.5)
    CHAR_HEIGHT = (LINE_HEIGHT)*100/72  # Font 'height' to digit height ratio for Helvetica
    width = page.stringWidth('10', "Helvetica", CHAR_HEIGHT)
    if width > COLL_WIDTH * 1.0:        # If the width of '10' is more than the column width
        CHAR_HEIGHT = CHAR_HEIGHT * COLL_WIDTH * 1.0 / width
    # CHAR_HEIGHT = 0.8 * COLL_WIDTH
    debug(1, "Character height:", CHAR_HEIGHT, "Line height:", LINE_HEIGHT)

    return(TARGET_WIDTH, TARGET_HEIGHT, COLL_WIDTH, ROW_HEIGHT, N_BELLS, CHAR_HEIGHT, LINE_HEIGHT)

# ---


def process_row(y):
    global DONE, LINE, BUFFER

    page.setStrokeGray(0.4)
    page.setLineWidth(BAR_LINE)
    page.rect(H_MARGIN, y, TARGET_WIDTH, ROW_HEIGHT)
    for beat in range(1, BARS*BEATS):
        # ebug(2, beat, BEATS, PLANE_LINE, BAR_LINE)
        page.setLineWidth(BAR_LINE if beat % BEATS == 0 else PLAIN_LINE)
        debug(2, "Beet x:", H_MARGIN+(beat*COLL_WIDTH), "Beet y:", y)
        page.line(H_MARGIN+(beat*COLL_WIDTH), y, H_MARGIN+(beat*COLL_WIDTH), y+ROW_HEIGHT)

    beat = 0
    BUFFER = []
    while not DONE:

        line = LINE
        if line[0] in ('!', '/', '\\'):
            time_char = line[0]
            line = line[1:]
        else:
            time_char = ''

        partial = False
        if time_char == '!':
            offset = COLL_WIDTH/2
            partial = True
            debug(2, "Half beet")
        elif time_char == '/':
            beat += 1
            offset = -COLL_WIDTH/5
            partial = True
            debug(2, "Double beat, part 1")
        elif time_char == '\\':
            offset = COLL_WIDTH/5
            partial = True
            debug(2, "Double beat, part 2")
        else:
            beat += 1
            offset = 0
            debug(2, "Full beat")

        # have we gone off the current row?

        debug(2, "Current beat:", beat, "offset:", offset)
        if beat > (BEATS*BARS):
            break

        draw_bells(line, beat, offset, partial, y)

        LINE = read_line()

    page.setFillColor('black')
    for item in BUFFER:
        page.setFont(item[0], item[1])
        if item[2]:
            page.drawCentredString(item[3], item[4], item[5])
        else:
            page.drawString(item[3], item[4], item[5])

# ---


def draw_bells(line, beat, offset, partial, y):

    global BUFFER

    if line == '-':
        return

    for bell in line.split():

        if bell[0] == '*':
            font = "Helvetica-Bold"
            bell = bell[1:]
        else:
            font = "Helvetica"
        page.setFont(font, CHAR_HEIGHT)

        debug(3, "Plotting bell", bell)
        BELLS_USED.add(bell)
        nbell = int(re.sub(r'[^\d]', '', bell))
        assert FIRST <= nbell <= LAST, "Bell number bell outside declared range"
        h_pos = H_MARGIN + (COLL_WIDTH*(beat-0.5)) + offset
        # Visual centre of 10, 11, 12 is 2.5% to the right of the centreline
        if nbell >= 10:
            h_pos = h_pos - LINE_HEIGHT * 2.5 / 100
        v_pos = y+(LINE_HEIGHT*(LAST-nbell+0.25))
        match = re.search(r'([#,b])$', bell)
        # Special handling for sharps and flats
        if match:
            char = match.group(1)
            debug(3, "    Processing a", char)
            BUFFER.append((font, CHAR_HEIGHT, True, h_pos, v_pos, str(nbell)))
            # page.drawCentredString(h_pos, v_pos, str(nbell))
            width = page.stringWidth(str(nbell), font, CHAR_HEIGHT)
            BUFFER.append((font, CHAR_HEIGHT*0.8, False, h_pos+(width/2), v_pos+(CHAR_HEIGHT*0.4), char))
            # page.setFont(font, CHAR_HEIGHT*0.8)
            # page.drawString(h_pos+(width/2), v_pos+(CHAR_HEIGHT*0.4), char)
            # page.setFont(font, CHAR_HEIGHT)
        else:
            # Put a white box behind partial notes
            if partial:
                width = page.stringWidth(str(nbell), font, CHAR_HEIGHT)
                height = CHAR_HEIGHT * 72 / 100  # Font 'height' to digit height ratio for Helvetica
                page.setFillColor('white')
                page.rect(h_pos-(width/2.0), v_pos - (0.2 * height),
                          width, 1.4*height, stroke=0, fill=1)
            BUFFER.append((font, CHAR_HEIGHT, True, h_pos, v_pos, str(bell)))
            # page.setFillColor('black')
            # page.setFont(font, CHAR_HEIGHT)
            # page.drawCentredString(h_pos, v_pos, bell)
        debug(3, "    Plotting bell:", bell, "h_pos:", h_pos, "v_pos:", v_pos)

# ---


def process_page():
    global DONE, PAGE_COUNTER

    t1 = "%s (page %d)" % (TITLE, PAGE_COUNTER)
    if PAGE_COUNTER == 1:
        t1 = TITLE

    page.setFont("Helvetica-Bold", 30)
    page.drawCentredString(WIDTH/2, BOTTOM_MARGIN+TARGET_HEIGHT+0.5*HEADER, t1)

    # E.g. 2,1,0 for ROWS=3
    for row in range(ROWS-1, -1, -1):

        y = BOTTOM_MARGIN + (row*(ROW_HEIGHT+SEPERATOR))

        process_row(y)
        if DONE:
            break

    t2 = analyse_bells(BELLS_USED)

    page.setFont("Helvetica", 15)
    page.drawRightString(WIDTH-H_MARGIN, BOTTOM_MARGIN+TARGET_HEIGHT+0.5*HEADER, t2)

    page.setFont("Helvetica", 25)

    page.drawRightString(WIDTH-H_MARGIN, BOTTOM_MARGIN*0.5, "%s (%s)" % (t1, t2))

    offset = (WIDTH-(17.5*inch))/2.0
    draw_hole(offset, HEIGHT-(1*inch))
    draw_hole(WIDTH-(offset), HEIGHT-(1*inch))

    page.setFont("Helvetica", 15)
    page.drawCentredString(WIDTH/2, HEIGHT-(1*inch), datetime.datetime.now().isoformat(sep=' ', timespec='seconds'))

    PAGE_COUNTER += 1
    page.showPage()


def draw_hole(x, y):
    # Draw a hole marker centered on x,y

    radius = 0.25*inch
    page.setLineWidth(PLAIN_LINE)
    page.circle(x, y, radius)
    page.line(x-radius, y, x+radius, y)
    page.line(x, y-radius, x, y+radius)

# ---

# Echo: 0 - no output 1 - parameters 2 - info on each row
#       3 - info on each bell 4 - echo input


ECHO = 5

PAGESIZE = portrait(A1)
# PAGESIZE = (23.0*inch, 29.5*inch)
(WIDTH, HEIGHT) = PAGESIZE
debug(1, "Width:", WIDTH, "Height:", HEIGHT)
TOP_MARGIN = 1.75*inch
BOTTOM_MARGIN = 1*inch
H_MARGIN = 0.75*inch
HEADER = 0.5*inch
SEPERATOR = 0.25*inch

PLAIN_LINE = 1
BAR_LINE = 2

PAGE_COUNTER = 1
BELLS_USED = set()

input = fileinput.input()

(TITLE, BEATS, BARS, ROWS, FIRST, LAST) = process_header()

source = input.filename()
if source == '<stdin>':
    target = sys.stdout
else:
    base = os.path.splitext(source)[0]
    target = base + ".pdf"

page = canvas.Canvas(target, pagesize=PAGESIZE)

(TARGET_WIDTH, TARGET_HEIGHT, COLL_WIDTH, ROW_HEIGHT,
 N_BELLS, CHAR_HEIGHT, LINE_HEIGHT) = setup_parameters()

LINE = read_line()
assert not DONE, "Not even a beet of music"

while not DONE:
    process_page()

page.save()

if platform.system() == 'Windows':
    print("Press return to continue...")
    sys.stdin.readline()
