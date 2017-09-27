#!/bin/bash

# Pull data from MySQL server.

pushd "$HOME/upsdiagd/queries" >/dev/null || exit 1
  # shellcheck disable=SC1091
  source ./sql-includes || exit

  time mysql -h sql --skip-column-names -e \
  "USE domotica;                               \
  SELECT *                                     \
  FROM ups                                     \
  WHERE (sample_time >= NOW() - ${H_INTERVAL}) \
  GROUP BY (sample_epoch DIV ${H_DIVIDER})     \
  ;"                                           \
  | sed 's/\t/;/g;s/\n//g' > "${DATASTORE}/upsh.csv"
popd >/dev/null
