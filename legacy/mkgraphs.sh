#!/bin/bash

# Pull data from MySQL server and graph them.

LOCAL=$(date)
LOCALSECONDS=$(date -d "$LOCAL" +%s)
UTC=$(date -u -d "$LOCAL" +"%Y-%m-%d %H:%M:%S")  #remove timezone reference
UTCSECONDS=$(date -d "$UTC" +%s)
UTCOFFSET=$((LOCALSECONDS - UTCSECONDS))

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd "${SCRIPT_DIR}" >/dev/null || exit 1
  if [ "$(wc -l < /tmp/upsdiagd/mysql/upsd.csv)" -gt 5 ]; then
    # ups13 and ups14 are disabled, because the current UPS (EATON) does not supply
    # usable data for these graphs
    #echo -n "UPS13"
    #time gnuplot -e "utc_offset='${UTCOFFSET}'" ./graphs/ups13.gp
    #echo -n "UPS14"
    #time gnuplot -e "utc_offset='${UTCOFFSET}'" ./graphs/ups14.gp
    echo -n "UPS15"
    time timeout 120s gnuplot -e "utc_offset='${UTCOFFSET}'" ./graphs/ups15.gp
    echo -n "UPS16"
    time timeout 120s gnuplot -e "utc_offset='${UTCOFFSET}'" ./graphs/ups16.gp
    echo -n "UPS17"
    time timeout 120s gnuplot -e "utc_offset='${UTCOFFSET}'" ./graphs/ups17.gp
  fi
# shellcheck disable=SC2164
popd >/dev/null
