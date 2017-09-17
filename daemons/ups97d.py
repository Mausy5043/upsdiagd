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

from libdaemon import Daemon

# constants
DEBUG       = False
IS_JOURNALD = os.path.isfile('/bin/journalctl')
MYID        = "".join(list(filter(str.isdigit, os.path.realpath(__file__).split('/')[-1])))
MYAPP       = os.path.realpath(__file__).split('/')[-2]
NODE        = os.uname()[1]

class MyDaemon(Daemon):
  def run(self):
    try:                 # Initialise MySQLdb
      consql    = mdb.connect(host='sql.lan', db='domotica', read_default_file='~/.my.cnf')
      if consql.open:    # dB initialised succesfully -> get a cursor on the dB.
        cursql  = consql.cursor()
        cursql.execute("SELECT VERSION()")
        versql  = cursql.fetchone()
        cursql.close()
        logtext = "{0} : {1}".format("Attached to MySQL server", versql)
        syslog.syslog(syslog.LOG_INFO, logtext)
    except mdb.Error:
      syslog_trace("Unexpected MySQL error in run(init)", syslog.LOG_CRIT, DEBUG)
      syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
      if consql.open:    # attempt to close connection to MySQLdb
        consql.close()
        syslog_trace(" ** Closed MySQL connection in run() **", syslog.LOG_CRIT, DEBUG)
      raise

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

    # samples         = samplesperCycle * cycles              # total number of samples averaged
    sampleTime      = reportTime/samplesperCycle         # time [s] between samples
    # cycleTime       = samples * sampleTime                # time [s] per cycle

    while True:
      try:
        startTime   = time.time()

        do_sql_data(flock, iniconf, consql)

        waitTime    = sampleTime - (time.time() - startTime) - (startTime % sampleTime)
        if (waitTime > 0):
          syslog_trace("Waiting  : {0}s".format(waitTime), False, DEBUG)
          syslog_trace("................................", False, DEBUG)
          time.sleep(waitTime)
      except Exception:
        syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        # attempt to close connection to MySQLdb
        if consql.open:
          consql.close()
          syslog_trace(" *** Closed MySQL connection in run() ***", syslog.LOG_CRIT, DEBUG)
        raise

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    with open(filename, 'r') as f:
      ret = f.read().strip('\n')
  return ret

def do_writesample(cnsql, cmd, sample):
  fail2write  = False
  dat         = (sample.split(', '))
  try:
    cursql    = cnsql.cursor()
    syslog_trace("   Data: {0}".format(dat), False, DEBUG)
    cursql.execute(cmd, dat)
    cnsql.commit()
    cursql.close()
  except mdb.IntegrityError as e:
    syslog_trace("DB error : {0}".format(e.__str__), syslog.LOG_ERR,  DEBUG)
    if cursql:
      cursql.close()
      syslog_trace(" *** Closed MySQL connection in do_writesample() ***", syslog.LOG_ERR, DEBUG)
      syslog_trace(" Execution of MySQL command {0} FAILED!".format(cmd), syslog.LOG_INFO, DEBUG)
      syslog_trace(" Not added to MySQLdb: {0}".format(dat), syslog.LOG_INFO, DEBUG)
    pass

  return fail2write

def do_sql_data(flock, inicnfg, cnsql):
  syslog_trace("============================", False, DEBUG)
  syslog_trace("Pushing data to MySQL-server", False, DEBUG)
  syslog_trace("============================", False, DEBUG)
  unlock(flock)  # remove stale lock
  time.sleep(2)
  lock(flock)
  # wait for all other processes to release their locks.
  count_internal_locks = 2
  while (count_internal_locks > 1):
    time.sleep(1)
    count_internal_locks = 0
    for fname in glob.glob(r'/tmp/' + MYAPP + '/*.lock'):
      count_internal_locks += 1
    syslog_trace("{0} internal locks exist".format(count_internal_locks), False, DEBUG)
  # endwhile

  for inisect in inicnfg.sections():  # Check each section of the config.ini file
    errsql = False
    try:
      ifile = inicnfg.get(inisect, "resultfile")
      syslog_trace(" < {0}".format(ifile), False, DEBUG)

      try:
        sqlcmd = []
        sqlcmd = inicnfg.get(inisect, "sqlcmd")
        syslog_trace("   CMD : {0}".format(sqlcmd), False, DEBUG)

        data = cat(ifile).splitlines()
        if data:
          for entry in range(0, len(data)):
            errsql = do_writesample(cnsql, sqlcmd, data[entry])
          # endfor
        # endif
      except configparser.NoOptionError as e:  # no sqlcmd
        syslog_trace("*1* {0}".format(e.__str__), False, DEBUG)
    except configparser.NoOptionError as e:  # no ifile
      syslog_trace("*2* {0}".format(e.__str__), False, DEBUG)

    try:
      if not errsql:                     # SQL-job was successful or non-existing
        if os.path.isfile(ifile):        # IF resultfile exists
          syslog_trace("Deleting {0}".format(ifile), False, DEBUG)
          os.remove(ifile)
    except configparser.NoOptionError as e:  # no ofile
      syslog_trace("*3* {0}".format(e.__str__), False, DEBUG)

  # endfor
  unlock(flock)

def lock(fname):
  open(fname, 'a').close()
  syslog_trace("!..LOCK", False, DEBUG)

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)
    syslog_trace("!..UNLOCK", False, DEBUG)

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
