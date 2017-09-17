#!/bin/bash

# Pull data from MySQL server.

pushd "$HOME/upsdiagd" >/dev/null || exit 1
  # shellcheck disable=SC1091
  source ./sql-includes || exit

  time mysql -h sql.lan --skip-column-names -e  \
  "USE domotica;                                \
  SELECT *                                      \
  FROM ups                                      \
  WHERE (sample_time >= NOW() - ${D_INTERVAL})  \
    AND (sample_time <= NOW() - ${DH_INTERVAL}) \
  GROUP BY (sample_epoch DIV ${D_DIVIDER})      \
  ;"                                            \
  | sed 's/\t/;/g;s/\n//g' > "${DATASTORE}/upsd.csv"
popd >/dev/null
