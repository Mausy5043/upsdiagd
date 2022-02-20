#!/usr/bin/env python3

"""Data post-processor."""

import configparser
import os
import subprocess
import sys
import syslog
import time
import traceback

import mausy5043funcs.fileops3 as mf
from mausy5043libs.libdaemon3 import Daemon
from mausy5043libs.libgraph3 import Graph
from mausy5043libs.libsqldata3 import SqlDataFetch

# constants
DEBUG       = False
IS_JOURNALD = os.path.isfile('/bin/journalctl')
MYID        = "".join(list(filter(str.isdigit, os.path.realpath(__file__).split('/')[-1])))
MYAPP       = os.path.realpath(__file__).split('/')[-3]
MYAPPDIR    = "/".join(list(filter(str, os.path.realpath(__file__).split('/')[:-2])))
NODE        = os.uname()[1]
GRAPH_UPDATE    = 3    # in minutes
SQL_UPDATE_HOUR = GRAPH_UPDATE  # in minutes (shouldn't be shorter than GRAPH_UPDATE)
SQL_UPDATE_DAY  = 27  # in minutes
SQL_UPDATE_WEEK = 4   # in hours
SQL_UPDATE_YEAR = 8   # in hours

# initialise logging
syslog.openlog(ident=MYAPP, facility=syslog.LOG_LOCAL0)


class MyDaemon(Daemon):
  """Override Daemon-class run() function."""

  @staticmethod
  def run():
    """Execute main loop."""
    iniconf = configparser.ConfigParser()
    iniconf.read('/' + MYAPPDIR + '/config.ini')
    # flock       = iniconf.get(MYID, "lockfile")
    script_name = iniconf.get(MYID, "lftpscript")
    sample_time = iniconf.getint(MYID, "reporttime") / iniconf.getint(MYID, "samplespercycle")
    sqldata.fetch()
    if trendgraph.make() == 0:
      upload_page(script_name)
    while True:
      try:
        start_time   = time.time()

        do_stuff(script_name)

        pause_time    = sample_time - (time.time() - start_time) - (start_time % sample_time)
        if pause_time > 0:
          mf.syslog_trace("Waiting  : {0}s".format(pause_time), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(pause_time)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise


def do_stuff(script):
  """Run various scripts."""
  # wait 4 seconds for processes to finish
  # unlock(flock)  # remove stale lock
  time.sleep(4)

  # Retrieve data from MySQL database
  result = sqldata.fetch()
  mf.syslog_trace("...datafetch:  {0}".format(result), False, DEBUG)

  # Create the graphs based on the MySQL data
  result = trendgraph.make()
  mf.syslog_trace("...trendgrph:  {0}".format(result), False, DEBUG)
  if result == 0:
    upload_page(script)


def upload_page(script):
  """Upload the webpage."""
  try:
    # Upload the webpage and graphs
    if os.path.isfile('/tmp/' + MYAPP + '/site/default.md'):
      write_lftp(script)
      cmnd = ['lftp', '-f', script]
      mf.syslog_trace("...:  {0}".format(cmnd), False, DEBUG)
      cmnd = subprocess.check_output(cmnd, timeout=20)
      mf.syslog_trace("...uploadpag:  {0}".format(cmnd), False, DEBUG)
  except subprocess.TimeoutExpired:
    mf.syslog_trace("***TIMEOUT***:  {0}".format(cmnd), syslog.LOG_ERR, DEBUG)
    time.sleep(17 * 60)             # wait 17 minutes for the router to restart.
  except subprocess.CalledProcessError:
    mf.syslog_trace("***ERROR***:    {0}".format(cmnd), syslog.LOG_ERR, DEBUG)
    time.sleep(17 * 60)             # wait 17 minutes for the router to restart.


def write_lftp(script):
  """Output the webpage-upload-script."""
  with open(script, 'w') as file_handle:
    file_handle.write('# DO NOT EDIT\n')
    file_handle.write('# This file is created automatically by ' + MYAPP + '\n\n')
    file_handle.write('# lftp script\n\n')
    file_handle.write('set cmd:fail-exit yes;\n')
    file_handle.write('open hendrixnet.nl;\n')
    file_handle.write('cd 06.ups/;\n')
    file_handle.write('set cmd:fail-exit no;\n')
    file_handle.write('mirror --reverse --delete --verbose=3 -c /tmp/' + MYAPP + '/site/ . ;\n')
    file_handle.write('\n')


if __name__ == "__main__":
  daemon = MyDaemon('/tmp/' + MYAPP + '/' + MYID + '.pid')                                    # pylint: disable=C0103
  trendgraph = Graph(os.environ['HOME'] + '/' + MYAPP + '/mkgraphs.sh', GRAPH_UPDATE)         # pylint: disable=C0103
  sqldata = (SqlDataFetch(os.environ['HOME'] + '/' + MYAPP + '/queries',                      # pylint: disable=C0103
                          '/srv/semaphores',
                          SQL_UPDATE_HOUR, SQL_UPDATE_DAY, SQL_UPDATE_WEEK, SQL_UPDATE_YEAR))

  syslog.openlog(ident=MYAPP, facility=syslog.LOG_LOCAL0)                                     # initialise logging
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
