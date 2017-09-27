#!/usr/bin/env python3

# Communicates with the UPS.

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
NODE        = os.uname()[1]

# initialise logging
syslog.openlog(ident=MYAPP, facility=syslog.LOG_LOCAL0)

class MyDaemon(Daemon):
  """Definition of daemon."""
  @staticmethod
  def run():
    iniconf         = configparser.ConfigParser()
    inisection      = MYID
    home            = os.path.expanduser('~')
    s               = iniconf.read(home + '/' + MYAPP + '/config.ini')
    mf.syslog_trace("Config file   : {0}".format(s), False, DEBUG)
    mf.syslog_trace("Options       : {0}".format(iniconf.items(inisection)), False, DEBUG)
    reporttime      = iniconf.getint(inisection, "reporttime")
    cycles          = iniconf.getint(inisection, "cycles")
    samplespercycle = iniconf.getint(inisection, "samplespercycle")
    flock           = iniconf.get(inisection, "lockfile")
    fdata           = iniconf.get(inisection, "resultfile")

    samples         = samplespercycle * cycles           # total number of samples averaged
    sampletime      = reporttime/samplespercycle         # time [s] between samples

    data            = []                                 # array for holding sampledata
    # raw             = [0] * 8                            # array for holding previous

    while True:
      try:
        starttime     = time.time()

        result        = do_work()
        result        = result.split(',')
        mf.syslog_trace("Result   : {0}".format(result), False, DEBUG)
        # data.append(list(map(int, result)))
        data.append([float(d) for d in result])
        if (len(data) > samples):
          data.pop(0)
        mf.syslog_trace("Data     : {0}".format(data),   False, DEBUG)

        # report sample average
        if (starttime % reporttime < sampletime):
          # somma       = list(map(sum, zip(*data)))
          somma = [sum(d) for d in zip(*data)]
          # not all entries should be float
          # ['234.000', '13.700', '100.000', '20.000', '1447.000']
          averages = [float(format(d / len(data), '.3f')) for d in somma]
          mf.syslog_trace("Averages : {0}".format(averages),  False, DEBUG)
          do_report(averages, flock, fdata)

        waittime    = sampletime - (time.time() - starttime) - (starttime % sampletime)
        if (waittime > 0):
          mf.syslog_trace("Waiting  : {0}s".format(waittime), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(waittime)
        else:
          mf.syslog_trace("Behind   : {0}s".format(waittime), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise

def do_work():
  # 5 datapoints gathered here
  try:
    upsc = str(subprocess.check_output(['upsc', 'ups@localhost']), 'utf-8').splitlines()
  except subprocess.CalledProcessError:
    # mf.syslog_trace("Unexpected error in do_work()", syslog.LOG_CRIT, DEBUG)
    # mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
    syslog.syslog(syslog.LOG_ALERT, "Waiting 10s ...")

    time.sleep(10)    # wait to let the driver crash properly
    mf.syslog_trace("*** RESTARTING nut-driver.service ***", syslog.LOG_ALERT, DEBUG)
    r = str(subprocess.check_output(['sudo', 'systemctl', 'restart',  'nut-driver.service']), 'utf-8').splitlines()
    mf.syslog_trace("Returned : {0}".format(r), False, DEBUG)

    time.sleep(15)
    mf.syslog_trace("!!! Retrying communication with UPS !!!", syslog.LOG_ALERT, DEBUG)
    upsc = str(subprocess.check_output(['upsc', 'ups@localhost']), 'utf-8').splitlines()
    pass

  ups0 = -1.0
  for element in range(0, len(upsc) - 1):
    var = upsc[element].split(': ')
    if (var[0] == 'input.voltage'):
      ups0 = float(var[1])
    # if (var[0] == 'battery.voltage'):
    if (var[0] == 'output.voltage'):
      ups1 = float(var[1])
    if (var[0] == 'battery.charge'):
      ups2 = float(var[1])
    if (var[0] == 'ups.load'):
      ups3 = float(var[1])
    if (var[0] == 'battery.runtime'):
      ups4 = float(var[1])

  return '{0}, {1}, {2}, {3} ,{4}'.format(ups0, ups1, ups2, ups3, ups4)

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outdate  = time.strftime('%Y-%m-%dT%H:%M:%S')
  outepoch = int(time.strftime('%s'))
  # round to current minute to ease database JOINs
  # outEpoch = outEpoch - (outEpoch % 60)
  result   = ', '.join(map(str, result))
  mf.lock(flock)
  with open(fdata, 'a') as f:
    f.write('{0}, {1}, {2}\n'.format(outdate, outepoch, result))
  mf.unlock(flock)


if __name__ == "__main__":
  daemon = MyDaemon('/tmp/' + MYAPP + '/' + MYID + '.pid')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    elif 'foreground' == sys.argv[1]:
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
