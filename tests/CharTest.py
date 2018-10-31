#!/usr/bin/env python

from __future__ import print_function

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm

x = 5*inch
y = 3*inch

text = '12Mj'

height = 10*cm

page = canvas.Canvas("test.pdf", pagesize=landscape(A4))

page.setFont("Helvetica-Bold", height, leading=0)
width = page.stringWidth(text, "Helvetica-Bold", height)
page.drawCentredString(x,y,text)

page.circle(x, y, 2, stroke=1, fill=1)

page.setLineWidth(1)

p = page.beginPath()
p.moveTo(x,y)
p.lineTo(x+width/2, y)
p.lineTo(x+width/2, y+height)
p.lineTo(x-width/2, y+height)
p.lineTo(x-width/2, y)
p.lineTo(x,y)

width1 = page.stringWidth('1', "Helvetica-Bold", height)
p.moveTo(x-width/2+width1, y)
p.lineTo(x-width/2+width1, y+height)
width2 = page.stringWidth('12', "Helvetica-Bold", height)
p.moveTo(x-width/2+width2, y)
p.lineTo(x-width/2+width2, y+height)
widthM = page.stringWidth('12M', "Helvetica-Bold", height)
p.moveTo(x-width/2+widthM, y)
p.lineTo(x-width/2+widthM, y+height)


page.drawPath(p)

page.showPage()
page.save()
