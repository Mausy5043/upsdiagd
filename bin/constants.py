#!/usr/bin/env python3

import os

_MYHOME = os.environ["HOME"]
_DATABASE = '/srv/databases/upsdata.sqlite3'

if not os.path.isfile(_DATABASE):
    _DATABASE = '/srv/data/upsdata.sqlite3'
if not os.path.isfile(_DATABASE):
    _DATABASE = '/mnt/data/upsdata.sqlite3'
if not os.path.isfile(_DATABASE):
    _DATABASE = f'.local/upsdata.sqlite3'
if not os.path.isfile(_DATABASE):
    _DATABASE = f'{_MYHOME}/.sqlite3/upsdata.sqlite3'

UPS = {'database': _DATABASE,
       'sql_command': "INSERT INTO ups ("
                      "sample_time, sample_epoch, "
                      "volt_in, volt_bat, charge_bat, "
                      "load_ups, runtime_bat"
                      ")"
                      "VALUES (?, ?, ?, ?, ?, ?, ?)",
       'sql_table': "ups",
       'report_time': 60,
       'cycles': 3,
       'samplespercycle': 5
       }
