# MySQL script
# create table for ups  readings

USE domotica;

# Uncomment the following line for testing purposes
#DROP TABLE IF EXISTS ups;

CREATE TABLE `ups` (
  `sample_time`   datetime NOT NULL DEFAULT '2000-01-01 00:00:01',
  `sample_epoch`  bigint(20) unsigned,
  `volt_in`       float(6,3),
  `volt_bat`      float(6,3),
  `charge_bat`    float(6,3),
  `load_ups`      float(6,3),
  `runtime_bat`   float(5,1),
  PRIMARY KEY (`sample_time`),
  INDEX (`sample_epoch`)
  ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;
