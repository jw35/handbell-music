#!/usr/bin/perl

require "qd.pl";
require "StandardFile.pl";

# Echo: 0 - no output; 1 - parameters; 2 - info on each row;
#       3 - info on each bell; 4 - echo input

$ECHO = 5;
$TARGET_WIDTH = 72 * 11;
$TARGET_HEIGHT = 72 * 7.75;
$HEADER_MARGIN = 72 * 0.5;
$SEP_MARGIN = 72 * 0.25;
$LINE = 1;
$BAR_LINE = 2;

$PAGE_COUNTER = 0;

&open_datafile;

&process_header;

&setup_parameters;

$DONE = 0;
while (!$DONE)
{ &process_page;
}

&clean_up;

# ---------------------------------------------------------------

sub open_datafile
{ ($INFILE = &StandardFile::GetFile("Select file to process","TEXT")) ||
             die ("Cancelled");

  open (INFILE,$INFILE) || die ("Failed to open input file");

}

# ---------------------------------------------------------------

sub process_header
{ $line = &read_line;
  die "No title line" unless $line;
  $TITLE = $line;
  print STDERR "Title: $TITLE\n" if ($ECHO > 0);

  $line = &read_line;
  die "No initial parameters" unless $line;
  ($BEATS,$BARS,$ROWS,$FIRST,$LAST) = split(' ',$line);
  if ($ECHO > 0)
  { print STDERR "Beets per bar: $BEATS\n";
    print STDERR "Bars per line: $BARS\n";
    print STDERR "Lines per page: $ROWS\n";
    print STDERR "Bells from: $FIRST to $LAST\n";
  }

  $MUSIC_LINE = &read_line;
  die "Not even one beat of music!" unless $MUSIC_LINE;
}  
  
# ---------------------------------------------------------------

sub setup_parameters
{ local ($picture);

  $COLL_WIDTH = int($TARGET_WIDTH/($BARS*$BEATS));
  print STDERR "Collumn width: $COLL_WIDTH\n" if ($ECHO > 1);
  $ACTUAL_WIDTH = $BARS * $BEATS * $COLL_WIDTH;
  print "Target width: $TARGET_WIDTH; Actual width $ACTUAL_WIDTH\n" if ($ECHO > 1);
  $ROW_HEIGHT = int(($TARGET_HEIGHT - $HEADER_MARGIN - 
                                             (($ROWS-1)*$SEP_MARGIN))/$ROWS);
  print STDERR "Row height: $ROW_HEIGHT\n" if ($ECHO > 1);

  $ACTUAL_HEIGHT = ($ROWS * $ROW_HEIGHT) + $HEADER_MARGIN + 
                                            (($ROWS-1) * $SEP_MARGIN);
  print STDERR "Target height: $TARGET_HEIGHT; Actual height $ACTUAL_HEIGHT\n" if ($ECHO > 1);

  $N_BELLS = $LAST - $FIRST +1;
  print STDERR "Number of bells: $N_BELLS\n" if ($ECHO > 1);
  $CHAR_HEIGHT = 0.8 * $COLL_WIDTH;
  $LINE_HEIGHT = ($ROW_HEIGHT - $CHAR_HEIGHT - 5) / (($N_BELLS-1)/2);
  $CHAR_HEIGHT = $LINE_HEIGHT if $CHAR_HEIGHT > $LINE_HEIGHT;
#  $LINE_HEIGHT = ($ROW_HEIGHT-5) / (($N_BELLS+1)/2);
#  $CHAR_HEIGHT = ($LINE_HEIGHT > 0.8 * $COLL_WIDTH ? 0.8 * $COLL_WIDTH : $LINE_HEIGHT);
  print STDERR "Character height: $CHAR_HEIGHT, Line height: $LINE_HEIGHT\n" if ($ECHO > 1);
    
}

# ---------------------------------------------------------------

sub process_page
{ ++$PAGE_COUNTER;

  &qd::SetRect(*picture,0,0,$ACTUAL_WIDTH,$ACTUAL_HEIGHT);
  &qd::OpenPicture($picture);
  &qd::ClipRect($picture);
  &qd::TextFont($qd::HELVETICA);

  &qd::MoveTo(int(($ACTUAL_WIDTH/2)+0.5),$HEADER_MARGIN-10);
  &text_face($qd::BOLD);
  &qd::TextSize(30);

  if ($PAGE_COUNTER == 1)  
  { &qd::DrawString($TITLE);
  }
  else
  { &qd::DrawString("$TITLE (page $PAGE_COUNTER)");
  }

  &qd::TextSize(int($CHAR_HEIGHT));
  &text_face($qd::PLAIN);

  &draw_grid;

  &draw_bells;

  $OUTFILE = "$INFILE$PAGE_COUNTER";
  open(OUTFILE,">$OUTFILE") || die "Can't open outfile $OUTFILE";
  print OUTFILE &qd::ClosePicture;
  close OUTFILE;
  MacPerl::SetFileInfo("ART5","PICT",$OUTFILE);
  print STDERR "Finished processing page $PAGE_COUNTER\n" if ($ECHO > 0);

}

# ---------------------------------------------------------------

sub draw_grid
{ for ($row = 0; $row <= $ROWS-1; ++$row)
  { &qd::SetRect(*border,
                 0-($BAR_LINE/2),
                 $HEADER_MARGIN+($row*$ROW_HEIGHT)+($row*$SEP_MARGIN)-($BAR_LINE/2),
                 $ACTUAL_WIDTH-($BAR_LINE/2),
                 $HEADER_MARGIN+(($row+1)*$ROW_HEIGHT)+($row*$SEP_MARGIN)-($BAR_LINE/2));
    &qd::PenSize($BAR_LINE,$BAR_LINE);
    &qd::FrameRect($border); 

    for ($beat = 1; $beat < $BARS*$BEATS; ++$beat)
    { $ln_width = (($beat % $BEATS) == 0 ? $BAR_LINE : $LINE);
      &qd::MoveTo(($beat*$COLL_WIDTH)-($ln_width/2),
                  $HEADER_MARGIN+($row*$ROW_HEIGHT)+($row*$SEP_MARGIN)-($ln_width/2));
      
      &qd::PenSize($ln_width,$ln_width);
      &qd::Line(0,$ROW_HEIGHT-($ln_width));
    }
  }
}

                         
# ---------------------------------------------------------------

sub draw_bells
{

  &qd::PenSize(0,0);
  
# this routine alays starts with the first line to process 
# in $MUSIC_LINE

# for each row

  for ($row = 1; ($row <= $ROWS) && !$DONE; ++$row)

# for each beat

  { print "Processing row $row\n" if ($ECHO > 2);
    $beat = 0;
    until ($DONE)
    { $MUSIC_LINE =~ s/^([!\\\/])//;
      $time_char = $1;
      print "Time char: '$time_char'\n" if ($ECHO > 2);
      if ($time_char eq '!')
      { $offset = int(($COLL_WIDTH/2)+0.5);
        print STDERR "Half beat\n" if ($ECHO > 2);
      }
      elsif ($time_char eq '/')
      { ++$beat;
        $offset = int(-$COLL_WIDTH/5);
        print STDERR "Double beat, part 1\n" if ($ECHO > 2);
      }
      elsif ($time_char eq '\\')
      { $offset = int($COLL_WIDTH/5);
        print STDERR "Double beat, part 2\n" if ($ECHO > 2);
      }
      else
      { ++$beat;
        $offset = 0;
        print STDERR "Full beat\n" if ($ECHO > 2);
      }

# have we gone off the current line?

      print "Current beat: $beat; offset $offset\n" if ($ECHO > 2);
      last if $beat > ($BEATS*$BARS);

# otherwise plot the bells

      unless ($MUSIC_LINE =~ /\s*-\s*/)
      { @bells = split(' ',$MUSIC_LINE);

       foreach $bell (@bells)
       { $bell_number = $bell;
         $bell_number =~ s/[^\d]//;
         die "Bell number $bell outside declared range ($FIRST-$LAST)"
                          if (($bell_number < $FIRST) || ($bell_number > $LAST));
         $h_pos = int(($COLL_WIDTH*($beat-0.51))+$offset);
         $v_pos = int(($HEADER_MARGIN + 
                  (($row-1)*($ROW_HEIGHT + $SEP_MARGIN)) + 
                  $CHAR_HEIGHT +
                  ($LINE_HEIGHT*($bell_number-$FIRST)/2))+0.5);
         &qd::MoveTo($h_pos,$v_pos);
         &text_face(($bell =~ s/\*//) ? $qd::BOLD : $qd::PLAIN);
         &qd::DrawString($bell);
         print STDERR "    Plotting bell '$bell' at $h_pos,$v_pos\n" if ($ECHO > 3);
        }
      }

# get the next line

      $MUSIC_LINE = &read_line;
      $DONE = 1 unless defined $MUSIC_LINE;           

    }

  }

}
     
# ---------------------------------------------------------------

sub clean_up
{
}

# ---------------------------------------------------------------

sub read_line
{ local ($line);
  while(1)
  { $line = <INFILE>;
    return undef unless $line;
    chomp ($line);
    print STDERR "Read_line: $line\n" if ($ECHO > 4);
    next if $line =~ /(^#)|(^$)/;
    return $line;
  }
}

# ---------------------------------------------------------------

sub text_face
{ local($face) = @_;
  return if $face == $current_face;
  &qd::TextFace($face);
  $current_face = $face;
}

