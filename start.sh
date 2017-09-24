#!/bin/bash

# restart.sh is run periodically by a cronjob.
# It checks the state of and (re-)starts daemons if they are not (yet) running.

HOSTNAME=$(hostname)
BRANCH=$(cat "$HOME/.upsdiagd.branch")

# make sure working tree exists
if [ ! -d /tmp/upsdiagd/site/img ]; then
  mkdir -p /tmp/upsdiagd/site/img
  chmod -R 755 /tmp/upsdiagd
fi
# make sure working tree exists
if [ ! -d /tmp/upsdiagd/mysql ]; then
  mkdir -p /tmp/upsdiagd/mysql
  chmod -R 755 /tmp/upsdiagd
fi

pushd "$HOME/upsdiagd" || exit 1
  # shellcheck disable=SC1091
  source ./includes

  # Check if DIAG daemons are running
  for daemon in $diaglist; do
    if [ -e "/tmp/upsdiagd/${daemon}.pid" ]; then
      if ! kill -0 $(cat "/tmp/upsdiagd/${daemon}.pid")  > /dev/null 2>&1; then
        logger -p user.err -t upsdiagd-restarter "  * Stale daemon ${daemon} pid-file found."
        rm "/tmp/upsdiagd/${daemon}.pid"
          echo "  * Start DIAG ${daemon}"
        eval "./daemons/ups${daemon}d.py restart"
      fi
    else
      logger -p user.notice -t upsdiagd-restarter "Found daemon ${daemon} not running."
        echo "  * Start UPS ${daemon}"
      eval "./daemons/ups${daemon}d.py restart"
    fi
  done

  # Check if SVC daemons are running
  for daemon in $srvclist; do
    if [ -e "/tmp/upsdiagd/${daemon}.pid" ]; then
      if ! kill -0 $(cat "/tmp/upsdiagd/${daemon}.pid")  > /dev/null 2>&1; then
        logger -p user.err -t upsdiagd-restarter "* Stale daemon ${daemon} pid-file found."
        rm "/tmp/upsdiagd/${daemon}.pid"
          echo "  * Start UPSVC ${daemon}"
        eval "./daemons/ups${daemon}d.py restart"
      fi
    else
      logger -p user.notice -t upsdiagd-restarter "Found daemon ${daemon} not running."
        echo "  * Start UPSVC ${daemon}"
      eval "./daemons/ups${daemon}d.py restart"
    fi
  done
popd
