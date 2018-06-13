#!/usr/bin/env python3

# daemon97.py pushes data to the MySQL-server.

import configparser
import glob
import MySQLdb as mdb
import os
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
    try:                 # Initialise MySQLdb
      consql    = mdb.connect(host='sql', db='domotica', read_default_file='~/.my.cnf')
      if consql.open:    # dB initialised succesfully -> get a cursor on the dB.
        cursql  = consql.cursor()
        cursql.execute("SELECT VERSION()")
        versql  = cursql.fetchone()
        cursql.close()
        logtext = "{0} : {1}".format("Attached to MySQL server", versql)
        syslog.syslog(syslog.LOG_INFO, logtext)
    except mdb.Error:
      mf.syslog_trace("Unexpected MySQL error in run(init)", syslog.LOG_CRIT, DEBUG)
      mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
      if consql.open:    # attempt to close connection to MySQLdb
        consql.close()
        mf.syslog_trace(" ** Closed MySQL connection in run() **", syslog.LOG_CRIT, DEBUG)
      raise

    iniconf         = configparser.ConfigParser()
    inisection      = MYID
    s               = iniconf.read('/' + MYAPPDIR + '/config.ini')
    mf.syslog_trace("Config file   : {0}".format(s), False, DEBUG)
    mf.syslog_trace("Options       : {0}".format(iniconf.items(inisection)), False, DEBUG)
    reporttime      = iniconf.getint(inisection, "reporttime")
    # cycles          = iniconf.getint(inisection, "cycles")
    samplespercycle = iniconf.getint(inisection, "samplespercycle")
    flock           = iniconf.get(inisection, "lockfile")

    # samples         = samplesperCycle * cycles              # total number of samples averaged
    sampletime      = reporttime/samplespercycle         # time [s] between samples
    # cycleTime       = samples * sampleTime                # time [s] per cycle

    while True:
      try:
        starttime   = time.time()

        do_sql_data(flock, iniconf, consql)

        waittime    = sampletime - (time.time() - starttime)  # - (starttime % sampletime)
        if (waittime > 0):
          mf.syslog_trace("Waiting  : {0}s".format(waittime), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(waittime)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        # attempt to close connection to MySQLdb
        if consql.open:
          consql.close()
          mf.syslog_trace(" *** Closed MySQL connection in run() ***", syslog.LOG_CRIT, DEBUG)
        raise


def do_writesample(cnsql, cmd, sample):
  fail2write  = False
  dat         = (sample.split(', '))
  try:
    cursql    = cnsql.cursor()
    mf.syslog_trace("   Data: {0}".format(dat), False, DEBUG)
    cursql.execute(cmd, dat)
    cnsql.commit()
    cursql.close()
  except mdb.IntegrityError as e:
    mf.syslog_trace("DB error : {0}".format(e.__str__), syslog.LOG_ERR,  DEBUG)
    if cursql:
      cursql.close()
      mf.syslog_trace(" *** Closed MySQL connection in do_writesample() ***", syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" Execution of MySQL command {0} FAILED!".format(cmd), syslog.LOG_INFO, DEBUG)
      mf.syslog_trace(" Not added to MySQLdb: {0}".format(dat), syslog.LOG_INFO, DEBUG)
    pass

  return fail2write


def do_sql_data(flock, inicnfg, cnsql):
  mf.syslog_trace("============================", False, DEBUG)
  mf.syslog_trace("Pushing data to MySQL-server", False, DEBUG)
  mf.syslog_trace("============================", False, DEBUG)
  mf.unlock(flock)  # remove stale lock
  time.sleep(2)
  mf.lock(flock)
  # wait for all other processes to release their locks.
  count_internal_locks = 2
  while (count_internal_locks > 1):
    time.sleep(1)
    count_internal_locks = 0
    for fname in glob.glob(r'/tmp/' + MYAPP + '/*.lock'):
      count_internal_locks += 1
    mf.syslog_trace("{0} internal locks exist".format(count_internal_locks), False, DEBUG)
  # endwhile

  for inisect in inicnfg.sections():  # Check each section of the config.ini file
    errsql = False
    try:
      ifile = inicnfg.get(inisect, "resultfile")
      mf.syslog_trace(" < {0}".format(ifile), False, DEBUG)

      try:
        sqlcmd = []
        sqlcmd = inicnfg.get(inisect, "sqlcmd")
        mf.syslog_trace("   CMD : {0}".format(sqlcmd), False, DEBUG)

        data = mf.cat(ifile).splitlines()
        if data:
          for entry in range(0, len(data)):
            errsql = do_writesample(cnsql, sqlcmd, data[entry])
          # endfor
        # endif
      except configparser.NoOptionError as e:  # no sqlcmd
        mf.syslog_trace("*1* {0}".format(e.__str__), False, DEBUG)
    except configparser.NoOptionError as e:  # no ifile
      mf.syslog_trace("*2* {0}".format(e.__str__), False, DEBUG)

    try:
      if not errsql:                     # SQL-job was successful or non-existing
        if os.path.isfile(ifile):        # IF resultfile exists
          mf.syslog_trace("Deleting {0}".format(ifile), False, DEBUG)
          os.remove(ifile)
    except configparser.NoOptionError as e:  # no ofile
      mf.syslog_trace("*3* {0}".format(e.__str__), False, DEBUG)

  # endfor
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
