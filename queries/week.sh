#!/bin/bash

# Pull data from MySQL server.

pushd "$HOME/upsdiagd/queries" >/dev/null || exit 1
  # shellcheck disable=SC1091
  source ./sql-includes || exit

  time mysql -h sql --skip-column-names -e  \
  "USE domotica;                                \
  SELECT MIN(sample_epoch),                     \
    MIN(volt_in),                               \
    AVG(volt_in),                               \
    MAX(volt_in),                               \
    MIN(volt_bat),                              \
    AVG(volt_bat),                              \
    MAX(volt_bat),                              \
    MIN(charge_bat),                            \
    AVG(charge_bat),                            \
    MAX(charge_bat),                            \
    MIN(load_ups),                              \
    AVG(load_ups),                              \
    MAX(load_ups),                              \
    MIN(runtime_bat),                           \
    AVG(runtime_bat),                           \
    MAX(runtime_bat)                            \
  FROM ups                                      \
  WHERE (sample_time >= NOW() - ${W_INTERVAL})  \
    AND (sample_time <= NOW() - ${WD_INTERVAL}) \
  GROUP BY (sample_epoch DIV ${W_DIVIDER})      \
  ;"                                            \
  | sed 's/\t/;/g;s/\n//g' > "${DATASTORE}/upsw.csv"
popd >/dev/null
