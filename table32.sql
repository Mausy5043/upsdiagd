# MySQL script
# create table for ups  readings

USE domotica;

DROP TABLE IF EXISTS ups;

CREATE TABLE `ups` (
  `sample_time`   datetime,
  `sample_epoch`  bigint(20) unsigned,
  `volt_in`       float(6,3),
  `volt_bat`      float(5,3),
  `charge_bat`    float(6,3),
  `load_ups`      float(5,3),
  `runtime_bat`   float(5,1),
  PRIMARY KEY (`sample_time`),
  INDEX (`sample_epoch`)
  ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;
