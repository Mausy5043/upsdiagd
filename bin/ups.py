#!/usr/bin/env python3

"""
Communicate with the UPS.

Store data from a supported UPS in an sqlite3 database.
"""

import configparser
import datetime as dt
import os
import sqlite3
import subprocess
import sys
import syslog
import time
import traceback

import mausy5043funcs.fileops3 as mf  # noqa
import mausy5043libs.libsignals3 as ml  # noqa

# constants
DEBUG = False
HERE = os.path.realpath(__file__).split('/')
# runlist id :
MYID = HERE[-1]
# app_name :
MYAPP = HERE[-3]
MYROOT = "/".join(HERE[0:-3])
# host_name :
NODE = os.uname()[1]


# example values:
# HERE: ['', 'home', 'pi', 'upsdiagdd', 'bin', 'ups.py']
# MYID: 'ups.py
# MYAPP: upsdiagd
# MYROOT: /home/pi
# NODE: rbups


def main():
    """Execute main loop."""
    global DEBUG
    global MYAPP
    global MYID
    global MYROOT
    killer = ml.GracefulKiller()
    iniconf = configparser.ConfigParser()
    iniconf.read(f'{MYROOT}/{MYAPP}/config.ini')
    report_time = iniconf.getint(MYID, 'reporttime')
    fdatabase = f"{MYROOT}/{iniconf.get('DEFAULT', 'databasefile')}"
    sqlcmd = iniconf.get(MYID, 'sqlcmd')
    samples_averaged = iniconf.getint(MYID, 'samplespercycle') * iniconf.getint(MYID, 'cycles')
    sample_time = report_time / iniconf.getint(MYID, 'samplespercycle')
    data = []

    test_db_connection(fdatabase)

    pause_time = time.time()
    while not killer.kill_now:
        if time.time() > pause_time:
            start_time = time.time()
            result = do_work()
            mf.syslog_trace(f"Result   : {result}", False, DEBUG)
            data.append([float(d) for d in result])
            if len(data) > samples_averaged:
                data.pop(0)

            # report sample average
            if start_time % report_time < sample_time:
                # somma       = list(map(sum, zip(*data)))
                somma = [sum(d) for d in zip(*data)]
                # not all entries should be float
                # ['234.000', '13.700', '100.000', '20.000', '1447.000']
                averages = [float(format(d / len(data), '.3f')) for d in somma]
                mf.syslog_trace("Averages : {0}".format(averages), False, DEBUG)
                do_add_to_database(averages, fdatabase, sqlcmd)

            pause_time = (sample_time
                          - (time.time() - start_time)
                          - (start_time % sample_time)
                          + time.time())
            if pause_time > 0:
                mf.syslog_trace(f"Waiting  : {pause_time - time.time():.1f}s", False, DEBUG)
                mf.syslog_trace("................................", False, DEBUG)
            else:
                mf.syslog_trace(f"Behind   : {pause_time - time.time():.1f}s", False, DEBUG)
                mf.syslog_trace("................................", False, DEBUG)
        else:
            time.sleep(1.0)


def do_work():
    """Do the thing.
    Example:
    *2*  battery.charge: 100
        battery.charge.low: 20
    *4*  battery.runtime: 1875
        battery.type: PbAc
        device.mfr: EATON
        device.model: Protection Station 650
        device.serial: AN2E49008
        device.type: ups
        driver.name: usbhid-ups
        driver.parameter.pollfreq: 30
        driver.parameter.pollinterval: 2
        driver.parameter.port: auto
        driver.parameter.synchronous: no
        driver.version: 2.7.4
        driver.version.data: MGE HID 1.39
        driver.version.internal: 0.41
        input.transfer.high: 264
        input.transfer.low: 184
        outlet.1.desc: PowerShare Outlet 1
        outlet.1.id: 2
        outlet.1.status: on
        outlet.1.switchable: no
        outlet.2.desc: PowerShare Outlet 2
        outlet.2.id: 3
        outlet.2.status: on
        outlet.2.switchable: no
        outlet.desc: Main Outlet
        outlet.id: 1
        outlet.power: 25
        outlet.switchable: no
        output.frequency.nominal: 50
    *0*  output.voltage: 230.0
        output.voltage.nominal: 230
        ups.beeper.status: enabled
        ups.delay.shutdown: 20
        ups.delay.start: 30
        ups.firmware: 1.13
    *3*  ups.load: 2
        ups.mfr: EATON
        ups.model: Protection Station 650
        ups.power.nominal: 650
        ups.productid: ffff
        ups.serial: AN2E49008
        ups.status: OL
        ups.timer.shutdown: -1
        ups.timer.start: -1
        ups.vendorid: 0463
    """
    # 5 datapoints gathered here
    try:
        upsc = str(subprocess.check_output(['upsc', 'ups@localhost'],
                                           stderr=subprocess.STDOUT),
                   'utf-8').splitlines()
    except subprocess.CalledProcessError:
        syslog.syslog(syslog.LOG_ALERT, "Waiting 10s ...")

        time.sleep(10)  # wait to let the driver crash properly
        mf.syslog_trace("*** RESTARTING nut-server.service ***", syslog.LOG_ALERT, DEBUG)
        redo = str(subprocess.check_output(['sudo', 'systemctl', 'restart', 'nut-server.service']),
                   'utf-8').splitlines()
        mf.syslog_trace("Returned : {0}".format(redo), False, DEBUG)

        time.sleep(15)
        mf.syslog_trace("!!! Retrying communication with UPS !!!", syslog.LOG_ALERT, DEBUG)
        upsc = str(subprocess.check_output(['upsc', 'ups@localhost'],
                                           stderr=subprocess.STDOUT),
                   'utf-8').splitlines()

    ups_data = [-1.0, -1.0, -1.0, -1.0, -1.0]
    for element in upsc:
        var = element.split(': ')
        # if var[0] == 'input.voltage':
        if var[0] == 'output.voltage':
            ups_data[0] = float(var[1])
        if var[0] == 'battery.voltage':  # not available on Eaton Protection Station
            ups_data[1] = float(var[1])
        if var[0] == 'battery.charge':
            ups_data[2] = float(var[1])
        if var[0] == 'ups.load':
            ups_data[3] = float(var[1])
        if var[0] == 'battery.runtime':
            ups_data[4] = float(var[1])

    return ups_data


def do_add_to_database(result, fdatabase, sql_cmd):
    """Commit the results to the database."""
    # Get the time and date in human-readable form and UN*X-epoch...
    conn = None
    cursor = None
    dt_format = '%Y-%m-%d %H:%M:%S'
    out_date = dt.datetime.now()  # time.strftime('%Y-%m-%dT%H:%M:%S')
    out_epoch = int(out_date.timestamp())
    results = (out_date.strftime(dt_format), out_epoch,
               result[0], result[1], result[2],
               result[3], result[4])
    mf.syslog_trace(f"   @: {out_date.strftime(dt_format)}", False, DEBUG)
    mf.syslog_trace(f"    : {results}", False, DEBUG)

    retries = 10
    while retries:
        retries -= 1
        try:
            conn = create_db_connection(fdatabase)
            cursor = conn.cursor()
            cursor.execute(sql_cmd, results)
            cursor.close()
            conn.commit()
            conn.close()
            retries = 0
        except sqlite3.OperationalError:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            if retries:
                raise


def create_db_connection(database_file):
    """
    Create a database connection to the SQLite3 database specified by database_file.
    """
    consql = None
    mf.syslog_trace(f"Connecting to: {database_file}", False, DEBUG)
    try:
        consql = sqlite3.connect(database_file, timeout=9000)
        return consql
    except sqlite3.Error:
        mf.syslog_trace("Unexpected SQLite3 error when connecting to server.", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        if consql:  # attempt to close connection to SQLite3 server
            consql.close()
            mf.syslog_trace(" ** Closed SQLite3 connection. **", syslog.LOG_CRIT, DEBUG)
        raise


def test_db_connection(fdatabase):
    """
    Test & log database engine connection.
    """
    try:
        conn = create_db_connection(fdatabase)
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        versql = cursor.fetchone()
        cursor.close()
        conn.commit()
        conn.close()
        syslog.syslog(syslog.LOG_INFO, f"Attached to SQLite3 server: {versql}")
    except sqlite3.Error:
        mf.syslog_trace("Unexpected SQLite3 error during test.", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise


if __name__ == "__main__":
    # initialise logging
    syslog.openlog(ident=f'{MYAPP}.{MYID.split(".")[0]}', facility=syslog.LOG_LOCAL0)

    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            main()
        elif sys.argv[1] == 'restart':
            main()
        elif sys.argv[1] == 'debug':
            # assist with debugging.
            DEBUG = True
            mf.syslog_trace("Debug-mode started.", syslog.LOG_DEBUG, DEBUG)
            print("Use <Ctrl>+C to stop.")
            main()
        else:
            print("Unknown command")
            sys.exit(2)
    else:
        print("usage: {0!s} start|restart|debug".format(sys.argv[0]))
        sys.exit(2)
    print("And it's goodnight from him")
    sys.exit(0)
