#!/usr/bin/env python3

# daemon82d.py creates an MD-file.

import configparser
import os
import platform
import shutil
import subprocess
import sys
import syslog
import time
import traceback

from libdaemon import Daemon

# constants
DEBUG       = False
IS_JOURNALD = os.path.isfile('/bin/journalctl')
MYID        = "".join(list(filter(str.isdigit, os.path.realpath(__file__).split('/')[-1])))
MYAPP       = os.path.realpath(__file__).split('/')[-2]
NODE        = os.uname()[1]

class MyDaemon(Daemon):
  def run(self):
    iniconf         = configparser.ConfigParser()
    inisection      = MYID
    home            = os.path.expanduser('~')
    s               = iniconf.read(home + '/' + MYAPP + '/config.ini')
    syslog_trace("Config file   : {0}".format(s), False, DEBUG)
    syslog_trace("Options       : {0}".format(iniconf.items(inisection)), False, DEBUG)
    reportTime      = iniconf.getint(inisection, "reporttime")
    # cycles          = iniconf.getint(inisection, "cycles")
    samplesperCycle = iniconf.getint(inisection, "samplespercycle")
    flock           = iniconf.get(inisection, "lockfile")
    fdata           = iniconf.get(inisection, "markdown")

    # samples         = samplesperCycle * cycles          # total number of samples averaged
    sampleTime      = reportTime/samplesperCycle        # time [s] between samples
    # cycleTime       = samples * sampleTime              # time [s] per cycle

    while True:
      try:
        startTime   = time.time()

        do_markdown(flock, fdata)

        waitTime    = sampleTime - (time.time() - startTime) - (startTime % sampleTime)
        if (waitTime > 0):
          syslog_trace("Waiting  : {0}s".format(waitTime), False, DEBUG)
          syslog_trace("................................", False, DEBUG)
          time.sleep(waitTime)
      except Exception:
        syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise

def do_markdown(flock, fdata):
  home              = os.path.expanduser('~')
  uname             = os.uname()

  fi = home + "/.upsdiagd.branch"
  with open(fi, 'r') as f:
    upsbranch  = f.read().strip('\n')

  lock(flock)
  shutil.copyfile(home + '/' + MYAPP + '/default.md', fdata)

  with open(fdata, 'a') as f:
    syslog_trace("writing {0}".format(fdata), False, DEBUG)

    f.write('![A GNUplot image should be here: ups13.png](img/ups13.png)\n')
    f.write('![A GNUplot image should be here: ups14.png](img/ups14.png)\n')
    f.write('![A GNUplot image should be here: ups15.png](img/ups15.png)\n')
    f.write('![A GNUplot image should be here: ups16.png](img/ups16.png)\n')
    f.write('![A GNUplot image should be here: ups17.png](img/ups17.png)\n')

    # System ID
    f.write('!!! ')
    f.write(uname[0] + ' ' + uname[1] + ' ' + uname[2] + ' ' + uname[3] + ' ' + uname[4] + ' ' + platform.platform() + '  \n')

    # branch
    f.write('!!! upsdiagd   on: ' + upsbranch + '\n\n')

    # upsc ups@localhost 2>/dev/null |grep -v "serial"
    upsc = str(subprocess.check_output(["upsc", "ups@localhost", "2>/dev/null"]), 'utf-8').splitlines()
    f.write('## UPS detail information')
    f.write(upsc + '\n')

  unlock(flock)

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

def syslog_trace(trace, logerr, out2console):
  # Log a python stack trace to syslog
  log_lines = trace.split('\n')
  for line in log_lines:
    if line and logerr:
      syslog.syslog(logerr, line)
    if line and out2console:
      print(line)

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
      syslog_trace("Daemon logging is ON", syslog.LOG_DEBUG, DEBUG)
      daemon.run()
    else:
      print("Unknown command")
      sys.exit(2)
    sys.exit(0)
  else:
    print("usage: {0!s} start|stop|restart|foreground".format(sys.argv[0]))
    sys.exit(2)
