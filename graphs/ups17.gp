#!/usr/bin/env gnuplot

# graph of UPS available run time

# datafiles
ifnameh = "/tmp/upsdiagd/mysql/upsh.csv"
ifnamed = "/tmp/upsdiagd/mysql/upsd.csv"
ifnamew = "/tmp/upsdiagd/mysql/upsw.csv"
ifnamey = "/tmp/upsdiagd/mysql/upsy.csv"
set output "/tmp/upsdiagd/site/img/ups17.png"

# ******************************************************* General settings *****
set terminal png enhanced font "Vera,9" size 1280,320
set datafile separator ';'
set datafile missing "NaN"    # Ignore missing values
set grid
tz_offset = utc_offset / 3600 # GNUplot only works with UTC. Need to compensate
                              # for timezone ourselves.
if (GPVAL_VERSION == 4.6) {epoch_compensate = 946684800} else {if (GPVAL_VERSION == 5.0) {epoch_compensate = 0}}
# Positions of split between graphs
LMARG = 0.06
LMPOS = 0.40
MRPOS = 0.73
RMARG = 0.94
TTPOS = 0.95
TBPOS = 0.55
BTPOS = 0.48
BBPOS = 0.08

min(x,y) = (x < y) ? x : y
max(x,y) = (x > y) ? x : y

# ********************************************************* Statistics (R) *****
# stats to be calculated here of column 2 (UX-epoch)
stats ifnameh using 1 name "X" nooutput

Xh_min = X_min + utc_offset - epoch_compensate
Xh_max = X_max + utc_offset - epoch_compensate

# stats to be calculated here for Y-axes
stats ifnameh using 6 name "Yh" nooutput

# ********************************************************* Statistics (M) *****
# stats to be calculated here of column 2 (UX-epoch)
stats ifnamed using 1 name "X" nooutput

Xd_min = X_min + utc_offset - epoch_compensate
Xd_max = X_max + utc_offset - epoch_compensate

# stats to be calculated here for Y-axes
stats ifnamed using 6 name "Yd" nooutput

# ********************************************************* Statistics (L) *****
# stats to be calculated here of column 2 (UX-epoch)
stats ifnamew using 1 name "X" nooutput
Xw_min = X_min + utc_offset - epoch_compensate
Xw_max = X_max + utc_offset - epoch_compensate

# stats for Y-axis
stats ifnamew using 6 name "Yw" nooutput

Ymax = max(max(Yd_max, Yh_max), Yw_max) + 10
Ymin = min(min(Yd_min, Yh_min), Yw_min) - 10

# ********************************************************* Statistics (Y) *****
# stats to be calculated here of column 2 (UX-epoch)
stats ifnamey using 1 name "X" nooutput
Xy_min = X_min + utc_offset - epoch_compensate
Xy_max = X_max + utc_offset - epoch_compensate

set multiplot layout 1, 3 title "Beschikbaarheid ".strftime("( %Y-%m-%dT%H:%M:%S )", time(0)+utc_offset)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                        TOP PLOT: past year
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

set tmargin at screen TTPOS
set bmargin at screen TBPOS
set lmargin at screen LMARG
set rmargin at screen RMARG

# ***************************************************************** X-axis *****
set xlabel "past year"       # X-axis label
set xdata time               # Data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%b"            # Display time in 24 hour notation on the X axis
set xrange [ Xy_min : Xy_max ]

# ***************************************************************** Y-axis *****
set ylabel "Tijd [s]"
set yrange [ : ]

# ***************************************************************** Legend *****
set key inside top left horizontal box
set key samplen 1
set key reverse Left

# ***************************************************************** Output *****

# ***** PLOT *****
plot ifnamey \
      using ($1+utc_offset):6 title " Tijd [s]" with lines lw 0.1 lc rgb "#ccbb0000"

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                       LEFT PLOT: past week
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

set tmargin at screen BTPOS
set bmargin at screen BBPOS
set lmargin at screen LMARG
set rmargin at screen LMPOS

# ***************************************************************** X-axis *****
set xlabel "past week"       # X-axis label
set xdata time               # Data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%a %d"            # Display time in 24 hour notation on the X axis
set xrange [ Xw_min : Xw_max ]

# ***************************************************************** Y-axis *****
set ylabel "Tijd [s]"
set yrange [ Ymin : Ymax ]

# ***************************************************************** Legend *****
unset key

# ***************************************************************** Output *****

# ***** PLOT *****
plot ifnamew \
      using ($1+utc_offset):6 title " Tijd [s]" with lines lw 0.1 fc rgb "#ccbb0000"
      # with points pt 5 ps 0.2 fc rgb "#ccbb0000" \



# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                     MIDDLE PLOT:  past day
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ***************************************************************** X-axis *****
set xlabel "past day"       # X-axis label
set xdata time               # Data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%R"            # Display time in 24 hour notation on the X axis
set xrange [ Xd_min : Xd_max ]

# ***************************************************************** Y-axis *****
set ylabel " "
set ytics format " "
set yrange [ Ymin : Ymax ]

# ***************************************************************** Legend *****
unset key

# ***************************************************************** Output *****
set lmargin at screen LMPOS+0.001
set rmargin at screen MRPOS

# ***** PLOT *****
plot ifnamed \
      using ($1+utc_offset):6 with lines lw 0.1 fc rgb "#ccbb0000"
      # with points pt 5 ps 0.2 fc rgb "#ccbb0000" \

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                      RIGHT PLOT: past hour
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ***************************************************************** X-axis *****
set xlabel "past hour"       # X-axis label
set xdata time               # Data on X-axis should be interpreted as time
set timefmt "%s"             # Time in log-file is given in Unix format
set format x "%R"            # Display time in 24 hour notation on the X axis
set xrange [ Xh_min : Xh_max ]
set xtics textcolor rgb "red"

# ***************************************************************** Y-axis *****
set ylabel " "
set ytics format " "
set yrange [ Ymin : Ymax ]

# ***************************************************************** Legend *****
unset key

# ***************************************************************** Output *****
set lmargin at screen MRPOS+0.001
set rmargin at screen RMARG

# ***** PLOT *****
plot ifnameh \
      using ($1+utc_offset):6 with lines lw 0.1 fc rgb "#ccbb0000"
      # with points pt 5 ps 0.2 fc rgb "#ccbb0000" \

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                                 FINALIZING
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

unset multiplot
