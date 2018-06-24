#!/bin/bash

# update.sh is run periodically by a cronjob.
# * It synchronises the local copy of upsdiagd with the current GitLab BRANCH
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

HOSTNAME="$(hostname)"
BRANCH="$(< "$HOME/.upsdiagd.branch")"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Wait for the daemons to finish their job. Prevents stale locks when restarting.
#echo "Waiting 30s..."
#sleep 30

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

pushd "${SCRIPT_DIR}" || exit 1
  # shellcheck disable=SC1091
  source ./includes
  git fetch origin
  # Check which files have changed
  DIFFLIST=$(git --no-pager diff --name-only "$BRANCH..origin/$BRANCH")
  git pull
  git fetch origin
  git checkout "$BRANCH"
  git reset --hard "origin/$BRANCH" && git clean -f -d
  # Set permissions
  chmod -R 744 ./*

  for fname in $DIFFLIST; do
    echo ">   $fname was updated from GIT"
    f5l4="${fname:0:11}${fname:${#fname}-4}"

    # Detect changes
    if [[ "$f5l4" == "daemons/upsd.py" ]]; then
      echo "  ! UPS daemon changed"
      eval "./$fname stop"
    fi

    #CONFIG.INI changed
    if [[ "$fname" == "config.ini" ]]; then
      echo "  ! Configuration file changed"
      echo "  o Restarting all ups daemons"
      for daemon in $upslist; do
        echo "  +- Restart ups$daemon"
        eval "./daemons/ups${daemon}d.py restart"
      done
      echo "  o Restarting all service daemons"
      for daemon in $srvclist; do
        echo "  +- Restart ups$daemon"
        eval "./daemons/ups${daemon}d.py restart"
      done
    fi
  done

  # Check if daemons are running
  for daemon in $upslist; do
    if [ -e "/tmp/upsdiagd/${daemon}.pid" ]; then
      if ! kill -0 "$(< "/tmp/upsdiagd/${daemon}.pid")"  > /dev/null 2>&1; then
        logger -p user.err -t upsdiagd "  * Stale daemon ${daemon} pid-file found."
        rm "/tmp/upsdiagd/${daemon}.pid"
          echo "  * Start DIAG ${daemon}"
        eval "./daemons/ups${daemon}d.py start"
      fi
    else
      logger -p user.warn -t upsdiagd "Found ups${daemon} not running."
        echo "  * Start ups${daemon}"
      eval "./daemons/ups${daemon}d.py start"
    fi
  done

  # Check if SVC daemons are running
  for daemon in $srvclist; do
    if [ -e "/tmp/upsdiagd/${daemon}.pid" ]; then
      if ! kill -0 "$(< "/tmp/upsdiagd/${daemon}.pid")"  > /dev/null 2>&1; then
        logger -p user.err -t upsdiagd "  * Stale daemon ${daemon} pid-file found."
        rm "/tmp/upsdiagd/${daemon}.pid"
          echo "  * Start ups${daemon}"
        eval "./daemons/ups${daemon}d.py start"
      fi
    else
      logger -p user.warn -t upsdiagd "Found ups${daemon} not running."
        echo "  * Start ups${daemon}"
      eval "./daemons/ups${daemon}d.py start"
    fi
  done
popd
