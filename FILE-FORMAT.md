Handbell File Format
====================

Music files are in plain text. Edit them with something like 'Notepad',
which is what you get if you double-click them.

Proces them by dragging and droping them onto `DisplayMusic`. Doing so will create a '.pdf' file.

Blank lines and lines starting '#' are ignored. It' a good idea
to separate blocks of notes and/or lines with one or other of these to make it easier
to find your way around the file. A '#' can be used to include a 'comment'
in the file.

The **first line** is the title.

The **second line** contains 5 numbers:

* The first is the number of beats in a bar
* The second is the number of bars on each line
* The third is the number of lines per page
* The fourth is the number of the highest bell
* The firth is the number of the lowest bell

All subsequent lines represent the bells striking for each beet. Each
bell is represented by its number. Follow a number with '#' or 'b' for
sharp or flat. Surround the number by '(' and ')' to print it in brackets.

In addition

* '-' is a rest
* A bell number preceded by '\*' is printed in bold
* A pair of rows, one starting '/' and one starting '\\'
will be printed side by side as one beet
* A row starting '!' will be printed on the line between one beet and
the next

For example:

```
In the Deep Midwinter
4 6 4 0 12

*3 8 12
/
\*2
*1
*3

*4 7 10
-
*5
-

*4 7 9 
/
\*3
*4
*7

*4 6 8
-
9
11

*3 8 12
/
\*2
*1
*3

*4 7 10
-
*5
-

*4 7 9
*3
*4 6 8
/
\*5
```