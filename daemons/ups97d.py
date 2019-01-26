#!/usr/bin/env python3

"""Pushes data to the MySQL-server."""

import configparser
import glob
import os
import sys
import syslog
import time
import traceback

import MySQLdb as mdb
import MySQLdb.constants.CR as mdbcr

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
    try:                 # Initialise MySQLdb
      consql    = mdb.connect(host='boson', db='domotica', read_default_file='~/.my.ups.cnf')
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

    iniconf = configparser.ConfigParser()
    iniconf.read('/' + MYAPPDIR + '/config.ini')
    flock       = iniconf.get(MYID, "lockfile")
    sample_time = iniconf.getint(MYID, "reporttime") / iniconf.getint(MYID, "samplespercycle")
    while True:
      try:
        start_time   = time.time()

        do_sql_data(flock, iniconf, consql)

        pause_time    = sample_time - (time.time() - start_time)  # - (start_time % sample_time)
        if pause_time > 0:
          mf.syslog_trace("Waiting  : {0}s".format(pause_time), False, DEBUG)
          mf.syslog_trace("................................", False, DEBUG)
          time.sleep(pause_time)
      except Exception:
        mf.syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        mf.syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        # attempt to close connection to MySQLdb
        if consql.open:
          consql.close()
          mf.syslog_trace(" *** Closed MySQL connection in run() ***", syslog.LOG_CRIT, DEBUG)
        raise


def do_writesample(cnsql, cmd, sample):
  """Commit data to database."""
  fail2write  = False
  dat         = (sample.split(', '))
  try:
    cursql    = cnsql.cursor()
    mf.syslog_trace("   Data: {0}".format(dat), False, DEBUG)
    cursql.execute(cmd, dat)
    cnsql.commit()
    cursql.close()
  except mdb.IntegrityError:
    mf.syslog_trace(" ***** MySQL ERROR *****", syslog.LOG_ERR, DEBUG)
    mf.syslog_trace(" *** DB error : {0}".format(sys.exc_info()[1]), syslog.LOG_ERR, DEBUG)
    if cursql:
      cursql.close()
      mf.syslog_trace(" *I* Closed MySQL connection in do_writesample()", syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" *** Execution of MySQL command {0} FAILED!".format(cmd), syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" *** Not added to MySQLdb: {0}".format(dat), syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" ***** MySQL ERROR *****", syslog.LOG_ERR, DEBUG)
  except mdb.OperationalError as mdb_error:
    mf.syslog_trace(" ***** MySQL ERROR *****", syslog.LOG_ERR, DEBUG)
    mf.syslog_trace(" *** DB error : {0}".format(sys.exc_info()[1]), syslog.LOG_ERR, DEBUG)
    fail2write = True
    if cursql:
      cursql.close()
      mf.syslog_trace(" *O* Closed MySQL connection in do_writesample()", syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" *** Execution of MySQL command {0} FAILED!".format(cmd), syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" *** Not added to MySQLdb: {0}".format(dat), syslog.LOG_ERR, DEBUG)
      mf.syslog_trace(" ***** MySQL ERROR *****", syslog.LOG_ERR, DEBUG)
    if mdb_error.args[0] in (mdbcr.SERVER_GONE_ERROR, mdbcr.SERVER_LOST):
      time.sleep(17 * 60)            # wait 17 minutes for the server to return.
      raise

  return fail2write


def do_sql_data(flock, inicnfg, cnsql):
  """Prepare data for pushing to the database."""
  mf.syslog_trace("============================", False, DEBUG)
  mf.syslog_trace("Pushing data to MySQL-server", False, DEBUG)
  mf.syslog_trace("============================", False, DEBUG)
  mf.unlock(flock)  # remove stale lock
  time.sleep(2)
  mf.lock(flock)
  # wait for all other processes to release their locks.
  count_internal_locks = 2
  while count_internal_locks > 1:
    time.sleep(1)
    count_internal_locks = len(glob.glob(r'/tmp/' + MYAPP + '/*.lock'))
    mf.syslog_trace("{0} internal locks exist".format(count_internal_locks), False, DEBUG)
  # endwhile

  for inisect in inicnfg.sections():  # Check each section of the config.ini file
    errsql = False
    try:
      ifile = inicnfg.get(inisect, "resultfile")
      # mf.syslog_trace(" < {0}".format(ifile), False, DEBUG)

      try:
        sqlcmd = []
        sqlcmd = inicnfg.get(inisect, "sqlcmd")
        # mf.syslog_trace("   CMD : {0}".format(sqlcmd), False, DEBUG)

        data = mf.cat(ifile).splitlines()
        if data:
          for entry in data:
            errsql = do_writesample(cnsql, sqlcmd, entry)
          # endfor
        # endif
      except configparser.NoOptionError as cp_error:  # no sqlcmd
        mf.syslog_trace("*1* {0}".format(cp_error.__str__), False, DEBUG)
    except configparser.NoOptionError as cp_error:  # no ifile
      mf.syslog_trace("*2* {0}".format(cp_error.__str__), False, DEBUG)

    try:
      if not errsql:                     # SQL-job was successful or non-existing
        if os.path.isfile(ifile):        # IF resultfile exists
          mf.syslog_trace("Deleting {0}".format(ifile), False, DEBUG)
          os.remove(ifile)
    except configparser.NoOptionError as cp_error:  # no ofile
      mf.syslog_trace("*3* {0}".format(cp_error.__str__), False, DEBUG)

  # endfor
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
