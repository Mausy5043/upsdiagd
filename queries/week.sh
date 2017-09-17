#!/bin/bash

# Pull data from MySQL server and graph them.

datastore="/tmp/upsdiagd/mysql"

if [ ! -d "$datastore" ]; then
  mkdir -p "$datastore"
fi

interval="INTERVAL 8 DAY "
# host=$(hostname)

pushd "$HOME/upsdiagd" >/dev/null
  mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT * FROM ups where (sample_time >=NOW() - $interval);" | sed 's/\t/;/g;s/\n//g' > "$datastore/upsw.csv"

  #http://www.sitepoint.com/understanding-sql-joins-mysql-database/
  #mysql -h sql.lan --skip-column-names -e "USE domotica; SELECT ds18.sample_time, ds18.sample_epoch, ds18.temperature, wind.speed FROM ds18 INNER JOIN wind ON ds18.sample_epoch = wind.sample_epoch WHERE (ds18.sample_time) >=NOW() - INTERVAL 1 MINUTE;" | sed 's/\t/;/g;s/\n//g' > $datastore/sql2c.csv
popd >/dev/null
