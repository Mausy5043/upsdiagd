#!/usr/bin/env python3

"""creates an MD-file."""

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
  """Override Daemon-class run() function."""

  @staticmethod
  def run():
    """Execute main loop."""
    iniconf = configparser.ConfigParser()
    iniconf.read('/' + MYAPPDIR + '/config.ini')
    flock       = iniconf.get(MYID, "lockfile")
    fdata       = iniconf.get(MYID, "markdown")
    sample_time = iniconf.getint(MYID, "reporttime") / iniconf.getint(MYID, "samplespercycle")

    while True:
      try:
        start_time = time.time()
        do_markdown(flock, fdata)

        pause_time = sample_time - (time.time() - start_time) - (start_time % sample_time)
        if pause_time > 0:
          mf.syslog_trace("Waiting  : {0}s".format(pause_time), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(pause_time)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise


def do_markdown(flock, fdata):
  """Create a MarkDown file."""
  uname = os.uname()

  branch_file = os.environ['HOME'] + "/.upsdiagd.branch"
  with open(branch_file, 'r') as file_handle:
    upsbranch  = file_handle.read().strip('\n')

  mf.lock(flock)
  shutil.copyfile('/' + MYAPPDIR + '/default.md', fdata)

  with open(fdata, 'a') as file_handle:
    mf.syslog_trace("writing {0}".format(fdata), False, DEBUG)

    # ups13 and ups14 are disabled, because the current UPS (EATON) does not supply
    # usable data for these graphs
    # file_handle.write('![A GNUplot image should be here: ups13.png](img/ups13.png)\n')
    # file_handle.write('![A GNUplot image should be here: ups14.png](img/ups14.png)\n')
    file_handle.write('![A GNUplot image should be here: ups16.png](img/ups16.png)\n')
    file_handle.write('![A GNUplot image should be here: ups15.png](img/ups15.png)\n')
    file_handle.write('![A GNUplot image should be here: ups17.png](img/ups17.png)\n')

    # System ID
    file_handle.write('!!! ')
    file_handle.write(uname[0] + ' ' + uname[2] + ' ' + uname[3] + ' ' + uname[4] + ' ' + platform.platform() + '  \n')

    # branch
    file_handle.write('!!! upsdiagd   on: ' + upsbranch + '  \n')
    file_handle.write('!!! ' + time.strftime("%Y.%m.%d %H:%M") + '\n\n')

    # upsc ups@localhost 2>/dev/null |grep -v "serial"
    upsc = str(subprocess.check_output(["upsc", "ups@localhost"]), 'utf-8').splitlines()
    file_handle.write('### UPS detail information\n\n')
    for ups_data in upsc:
      file_handle.write(ups_data + '  \n')

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
