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
  """Definition of daemon."""
  @staticmethod
  def run():
    iniconf         = configparser.ConfigParser()
    inisection      = MYID
    s               = iniconf.read('/' + MYAPPDIR + '/config.ini')
    mf.syslog_trace("Config file   : {0}".format(s), False, DEBUG)
    mf.syslog_trace("Options       : {0}".format(iniconf.items(inisection)), False, DEBUG)
    reporttime      = iniconf.getint(inisection, "reporttime")
    # cycles          = iniconf.getint(inisection, "cycles")
    samplespercycle = iniconf.getint(inisection, "samplespercycle")
    flock           = iniconf.get(inisection, "lockfile")
    fdata           = iniconf.get(inisection, "markdown")

    # samples         = samplesperCycle * cycles          # total number of samples averaged
    sampletime      = reporttime/samplespercycle        # time [s] between samples
    # cycleTime       = samples * sampleTime              # time [s] per cycle

    while True:
      try:
        starttime   = time.time()

        do_markdown(flock, fdata)

        waittime    = sampletime - (time.time() - starttime) - (starttime % sampletime)
        if (waittime > 0):
          mf.syslog_trace("Waiting  : {0}s".format(waittime), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(waittime)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise


def do_markdown(flock, fdata):
  home              = os.path.expanduser('~')
  uname             = os.uname()

  fi = home + "/.upsdiagd.branch"
  with open(fi, 'r') as f:
    upsbranch  = f.read().strip('\n')

  mf.lock(flock)
  shutil.copyfile('/' + MYAPPDIR + '/default.md', fdata)

  with open(fdata, 'a') as f:
    mf.syslog_trace("writing {0}".format(fdata), False, DEBUG)

    # ups13 and ups14 are disabled, because the current UPS (EATON) does not supply
    # usable data for these graphs
    # f.write('![A GNUplot image should be here: ups13.png](img/ups13.png)\n')
    # f.write('![A GNUplot image should be here: ups14.png](img/ups14.png)\n')
    f.write('![A GNUplot image should be here: ups15.png](img/ups15.png)\n')
    f.write('![A GNUplot image should be here: ups16.png](img/ups16.png)\n')
    f.write('![A GNUplot image should be here: ups17.png](img/ups17.png)\n')

    # System ID
    f.write('!!! ')
    f.write(uname[0] + ' ' + uname[2] + ' ' + uname[3] + ' ' + uname[4] + ' ' + platform.platform() + '  \n')

    # branch
    f.write('!!! upsdiagd   on: ' + upsbranch + '  \n')
    f.write('!!! ' + time.strftime("%Y.%m.%d %H:%M") + '\n\n')

    # upsc ups@localhost 2>/dev/null |grep -v "serial"
    upsc = str(subprocess.check_output(["upsc", "ups@localhost"]), 'utf-8').splitlines()
    f.write('### UPS detail information\n\n')
    for u in upsc:
      f.write(u + '  \n')

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
    elif 'debug' == sys.argv[1]:
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
