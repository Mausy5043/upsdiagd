#!/usr/bin/env sqlite3
# sqlite3 script
# create table for UPS readings

# Uncomment the following line for testing purposes
# DROP TABLE IF EXISTS ups;

CREATE TABLE IF NOT EXISTS ups (
  sample_time   datetime NOT NULL PRIMARY KEY,
  sample_epoch  integer,
  volt_in       real,
  volt_bat      real,
  charge_bat    real,
  load_ups      real,
  runtime_bat   integer
  );

# SQLite3 automatically creates a UNIQUE INDEX on the PRIMARY KEY in the background.
# So, no index needed.
