#!/bin/bash

# Pull data from MySQL server.

pushd "$HOME/upsdiagd/queries" >/dev/null || exit 1
  # shellcheck disable=SC1091
  source ./sql-includes || exit

  time mysql -h sql --skip-column-names -e  \
  "USE domotica;                                \
  SELECT MIN(sample_epoch),                     \
    AVG(volt_in),                               \
    AVG(volt_bat),                              \
    MIN(charge_bat),                            \
    MIN(load_ups),                              \
    MIN(runtime_bat)                            \
  FROM ups                                      \
  WHERE (sample_time >= NOW() - ${Y_INTERVAL})  \
    AND (sample_time <= NOW() - ${W_INTERVAL})  \
  GROUP BY YEAR(sample_time),                   \
           WEEK(sample_time, 3)                 \
  ;"                                            \
  | sed 's/\t/;/g;s/\n//g' > "${DATASTORE}/upsy.csv"
popd >/dev/null
