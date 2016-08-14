#!/usr/bin/env python3

# Communicates with the smart electricity meter [KAMSTRUP].
# This is all singular data, no averaging needed.

import configparser
import os
import re
import serial
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


port = serial.Serial()
port.baudrate = 9600
port.bytesize = serial.SEVENBITS
port.parity = serial.PARITY_EVEN
port.stopbits = serial.STOPBITS_ONE
port.xonxoff = 1
port.rtscts = 0
port.dsrdtr = 0
port.timeout = 15
port.port = "/dev/ttyUSB0"

class MyDaemon(Daemon):
  def run(self):
    iniconf         = configparser.ConfigParser()
    inisection      = MYID
    home            = os.path.expanduser('~')
    s               = iniconf.read(home + '/' + MYAPP + '/config.ini')
    syslog_trace("Config file   : {0}".format(s), False, DEBUG)
    syslog_trace("Options       : {0}".format(iniconf.items(inisection)), False, DEBUG)
    reportTime      = iniconf.getint(inisection, "reporttime")
    cycles          = iniconf.getint(inisection, "cycles")
    samplesperCycle = iniconf.getint(inisection, "samplespercycle")
    flock           = iniconf.get(inisection, "lockfile")
    fdata           = iniconf.get(inisection, "resultfile")

    samples         = samplesperCycle * cycles           # total number of samples averaged
    sampleTime      = reportTime/samplesperCycle         # time [s] between samples

    data            = []                                 # array for holding sampledata
    # raw             = [0] * 8                            # array for holding previous

    port.open()
    serial.XON
    while True:
      try:
        startTime     = time.time()

        result        = do_work()
        result        = result.split(',')
        syslog_trace("Result   : {0}".format(result), False, DEBUG)
        # data.append(list(map(int, result)))
        data.append([int(d) for d in result])
        if (len(data) > samples):
          data.pop(0)
        syslog_trace("Data     : {0}".format(data),   False, DEBUG)

        # report sample average
        if (startTime % reportTime < sampleTime):
          # somma       = list(map(sum, zip(*data)))
          somma = [sum(d) for d in zip(*data)]
          # not all entries should be float
          # ['3088596', '3030401', '270', '0', '0', '0', '1', '1']
          # averages    = [format(sm / len(data), '.2f') for sm in somma]
          averages = data[len(data)-1]
          averages[2]  = int(somma[2] / len(data))
          syslog_trace("Averages : {0}".format(averages),  False, DEBUG)
          do_report(averages, flock, fdata)

        waitTime    = sampleTime - (time.time() - startTime) - (startTime % sampleTime)
        if (waitTime > 0):
          syslog_trace("Waiting  : {0}s".format(waitTime), False, DEBUG)
          syslog_trace("................................", False, DEBUG)
          # no need to wait for the next cycles
          # the meter will pace the meaurements
          # any required waiting will be inside gettelegram()
          # time.sleep(waitTime)
        else:
          syslog_trace("Behind   : {0}s".format(waitTime), False, DEBUG)
          syslog_trace("................................", False, DEBUG)
      except Exception:
        syslog_trace("Unexpected error in run()", syslog.LOG_CRIT, DEBUG)
        syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
        raise

def do_work():
  electra1in  = 0
  electra2in  = 0
  powerin     = 0
  electra1out = 0
  electra2out = 0
  powerout    = 0
  tarif       = 0
  swits       = 1

  telegram, status = gettelegram()

  if status == 1:
    for element in range(0, len(telegram)):
      line = re.split('[\(\*\)]', telegram[element])
      # ['1-0:1.8.1', '00175.402', 'kWh', '']  T1 in
      if (line[0] == '1-0:1.8.1'):
        electra1in = int(float(line[1]) * 1000)
      # ['1-0:1.8.2', '00136.043', 'kWh', '']  T2 in
      if (line[0] == '1-0:1.8.2'):
        electra2in = int(float(line[1]) * 1000)
      # ['1-0:2.8.1', '00000.000', 'kWh', '']  T1 out
      if (line[0] == '1-0:2.8.1'):
        electra1out = int(float(line[1]) * 1000)
      # ['1-0:2.8.2', '00000.000', 'kWh', '']  T2 out
      if (line[0] == '1-0:2.8.2'):
        electra2out = int(float(line[1]) * 1000)
      # ['0-0:96.14.0', '0002', '']  tarif 1 or 2
      if (line[0] == '0-0:96.14.0'):
        tarif = int(line[1])
      # ['1-0:1.7.0', '0000.32', 'kW', '']  power in
      if (line[0] == '1-0:1.7.0'):
        powerin = int(float(line[1]) * 1000)
      # ['1-0:2.7.0', '0000.00', 'kW', ''] power out
      if (line[0] == '1-0:2.7.0'):
        powerout = int(float(line[1]) * 1000)
      # ['0-0:17.0.0', '999', 'A', '']
      # not recorded
      # ['0-0:96.3.10', '1', '']  powerusage (1) or powermanufacturing ()
      if (line[0] == '0-0:96.3.10'):
        swits = int(line[1])
      # ['0-0:96.13.1', '', '']
      # not recorded
      # ['0-0:96.13.0', '', '']
      # not recorded

  return '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}'.format(electra1in, electra2in, powerin, electra1out, electra2out, powerout, tarif, swits)

def gettelegram():
  # flag used to exit the while-loop
  abort = 0
  # countdown counter used to prevent infinite loops
  loops2go = 40
  # storage space for the telegram
  telegram = []
  # end of line delimiter
  # delim = "\x0a"

  while abort == 0:
    try:
      # line = "".join(iter(lambda: port.read(1), delim)).strip()
      line = str(port.readline().strip(), 'utf-8')
      if line == "!":
        abort = 1
      if line != "":
        telegram.append(line)
    except Exception:
      syslog_trace("*** Serialport read error:", syslog.LOG_CRIT, DEBUG)
      syslog_trace(traceback.format_exc(), syslog.LOG_CRIT, DEBUG)
      abort = 2

    loops2go = loops2go - 1
    if loops2go < 0:
      abort = 3

  # test for correct start of telegram
  if telegram[0][0] != "/":
    abort = 2

  # Return codes:
  # abort == 1 indicates a successful read
  # abort == 2 means that a serial port read/write error occurred
  # abort == 3 no valid data after several attempts
  return telegram, abort

def do_report(result, flock, fdata):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate  = time.strftime('%Y-%m-%dT%H:%M:%S')
  outEpoch = int(time.strftime('%s'))
  # round to current minute to ease database JOINs
  # outEpoch = outEpoch - (outEpoch % 60)
  result   = ', '.join(map(str, result))
  lock(flock)
  with open(fdata, 'a') as f:
    f.write('{0}, {1}, {2}\n'.format(outDate, outEpoch, result))
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
