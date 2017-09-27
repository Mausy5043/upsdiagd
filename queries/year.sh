#!/bin/bash

# Pull data from MySQL server.

pushd "$HOME/upsdiagd" >/dev/null || exit 1
  # shellcheck disable=SC1091
  source ./sql-includes || exit

  time mysql -h sql --skip-column-names -e  \
  "USE domotica;                                \
  SELECT *                                      \
  FROM ups                                      \
  WHERE (sample_time >= NOW() - ${Y_INTERVAL})  \
    AND (sample_time <= NOW() - ${W_INTERVAL})  \
  GROUP BY YEAR(sample_time),                   \
           WEEK(sample_time, 3)                 \
  ;"                                            \
  | sed 's/\t/;/g;s/\n//g' > "${DATASTORE}/upsy.csv"
popd >/dev/null
