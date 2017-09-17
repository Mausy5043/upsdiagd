#!/bin/bash

# Pull data from MySQL server and graph them.

LOCAL=$(date)
LOCALSECONDS=$(date -d "$LOCAL" +%s)
UTC=$(date -u -d "$LOCAL" +"%Y-%m-%d %H:%M:%S")  #remove timezone reference
UTCSECONDS=$(date -d "$UTC" +%s)
UTCOFFSET=$((LOCALSECONDS - UTCSECONDS))

pushd "$HOME/upsdiagd" >/dev/null
  if [ $(wc -l < /tmp/upsdiagd/mysql/upsd.csv) -gt 5 ]; then
    gnuplot -e "utc_offset='${UTCOFFSET}'" ./ups13.gp &
    gnuplot -e "utc_offset='${UTCOFFSET}'" ./ups14.gp &
    gnuplot -e "utc_offset='${UTCOFFSET}'" ./ups15.gp &
    gnuplot -e "utc_offset='${UTCOFFSET}'" ./ups16.gp &
    gnuplot -e "utc_offset='${UTCOFFSET}'" ./ups17.gp &
  fi

  wait

popd >/dev/null
