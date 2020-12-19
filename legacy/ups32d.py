#!/usr/bin/env python3

"""Communicate with the UPS and gather data."""

import configparser
import os
import sys
import syslog
import subprocess
import time
import traceback

from mausy5043libs.libdaemon3 import Daemon
import mausy5043funcs.fileops3 as mf

# constants
DEBUG       = False
IS_JOURNALD = os.path.isfile('/bin/journalctl')
MYID        = "".join(list(filter(str.isdigit, os.path.realpath(__file__).split('/')[-1])))
MYAPP       = os.path.realpath(__file__).split('/')[-3]
MYAPPDIR    = "/".join(list(filter(str, os.path.realpath(__file__).split('/')[:-2])))
NODE        = os.uname()[1]

# initialise logging
syslog.openlog(ident=MYAPP, facility=syslog.LOG_LOCAL0)


class MyDaemon(Daemon):
  """Override Daemon-class run() function."""

  @staticmethod
  def run():
    """Execute main loop."""
    iniconf          = configparser.ConfigParser()
    iniconf.read('/' + MYAPPDIR + '/config.ini')
    report_time      = iniconf.getint(MYID, "reporttime")
    flock            = iniconf.get(MYID, "lockfile")
    fdata            = iniconf.get(MYID, "resultfile")
    samples_averaged = iniconf.getint(MYID, "samplespercycle") * iniconf.getint(MYID, "cycles")
    sample_time      = report_time / iniconf.getint(MYID, "samplespercycle")

    data            = []                                 # array for holding sampledata

    while True:
      try:
        start_time = time.time()
        result = do_work()
        result = result.split(',')
        mf.syslog_trace("Result   : {0}".format(result), False, DEBUG)
        # data.append(list(map(int, result)))
        data.append([float(d) for d in result])
        if len(data) > samples_averaged:
          data.pop(0)
        mf.syslog_trace("Data     : {0}".format(data), False, DEBUG)

        # report sample average
        if start_time % report_time < sample_time:
          # somma       = list(map(sum, zip(*data)))
          somma = [sum(d) for d in zip(*data)]
          # not all entries should be float
          # ['234.000', '13.700', '100.000', '20.000', '1447.000']
          averages = [float(format(d / len(data), '.3f')) for d in somma]
          mf.syslog_trace("Averages : {0}".format(averages), False, DEBUG)
          do_report(averages, flock, fdata)

        pause_time    = (sample_time
                         - (time.time() - start_time)
                         - (start_time % sample_time))
        if pause_time > 0:
          mf.syslog_trace("Waiting  : {0}s".format(pause_time), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(pause_time)
        else:
          mf.syslog_trace("Behind   : {0}s".format(pause_time), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise


def do_work():
  """Do stuff."""
  # 5 datapoints gathered here
  try:
    upsc = str(subprocess.check_output(['upsc', 'ups@localhost']), 'utf-8').splitlines()
  except subprocess.CalledProcessError:
    syslog.syslog(syslog.LOG_ALERT, "Waiting 10s ...")

    time.sleep(10)    # wait to let the driver crash properly
    mf.syslog_trace("*** RESTARTING nut-server.service ***", syslog.LOG_ALERT, DEBUG)
    redo = str(subprocess.check_output(['sudo', 'systemctl', 'restart', 'nut-server.service']), 'utf-8').splitlines()
    mf.syslog_trace("Returned : {0}".format(redo), False, DEBUG)

    time.sleep(15)
    mf.syslog_trace("!!! Retrying communication with UPS !!!", syslog.LOG_ALERT, DEBUG)
    upsc = str(subprocess.check_output(['upsc', 'ups@localhost']), 'utf-8').splitlines()

  # ups0 and ups1 are disabled, because the current UPS (EATON) does not supply
  # usable data for these graphs
  ups0 = -1.0
  ups1 = -1.0
  for element in upsc:
    var = element.split(': ')
    # if var[0] == 'input.voltage':
    if var[0] == 'output.voltage':
      ups0 = float(var[1])
    if var[0] == 'battery.voltage':
      ups1 = float(var[1])
    if var[0] == 'battery.charge':
      ups2 = float(var[1])
    if var[0] == 'ups.load':
      ups3 = float(var[1]) * 10
    if var[0] == 'battery.runtime':
      ups4 = float(var[1])

  return '{0}, {1}, {2}, {3} ,{4}'.format(ups0, ups1, ups2, ups3, ups4)


def do_report(result, flock, fdata):
  """Push the results out to a file."""
  # Get the time and date in human-readable form and UN*X-epoch...
  out_date  = time.strftime('%Y-%m-%dT%H:%M:%S')
  out_epoch = int(time.strftime('%s'))
  # round to current minute to ease database JOINs
  # outEpoch = outEpoch - (outEpoch % 60)
  result   = ', '.join(map(str, result))
  mf.lock(flock)
  with open(fdata, 'a') as result_file:
    result_file.write('{0}, {1}, {2}\n'.format(out_date, out_epoch, result))
  mf.unlock(flock)


if __name__ == "__main__":
  daemon = MyDaemon('/tmp/' + MYAPP + '/' + MYID + '.pid')  # pylint: disable=C0103
  if len(sys.argv) == 2:
    if sys.argv[1] == 'start':
      daemon.start()
    elif sys.argv[1] == 'stop':
      daemon.stop()
    elif sys.argv[1] == 'restart':
      daemon.restart()
    elif sys.argv[1] == 'debug':
      # assist with debugging.
      print("Debug-mode started. Use <Ctrl>+C to stop.")
      DEBUG = True
      mf.syslog_trace("Daemon logging is ON", syslog.LOG_DEBUG, DEBUG)
      daemon.run()
    else:
      print("Unknown command")
      sys.exit(2)
    sys.exit(0)
  else:
    print("usage: {0!s} start|stop|restart|foreground".format(sys.argv[0]))
    sys.exit(2)
