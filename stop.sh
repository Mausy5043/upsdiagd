#!/bin/bash

# Use stop.sh to stop all daemons in one go
# You can use update.sh to get everything started ups.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd "${SCRIPT_DIR}" || exit 1
  # shellcheck disable=SC1091
  source ./includes

  # Check if DIAG daemons are running
  for daemon in $upslist; do
    # command the daemon to stop regardless if it is running or not.
    eval "./daemons/ups${daemon}d.py stop"
    # kill off any rogue daemons by the same name (it happens sometimes)
    if [   $(pgrep -fc "ups${daemon}d.py") -ne 0 ]; then
      kill $(pgrep -f  "ups${daemon}d.py")
    fi
    # log the activity
    logger -p user.err -t upsdiagd "  * Daemon ${daemon} stopped."
    # force rm the .pid file
    rm -f "/tmp/upsdiagd/${daemon}.pid"
  done

  # Check if SVC daemons are running
  for daemon in $srvclist; do
    # command the daemon to stop regardless if it is running or not.
    eval "./daemons/ups${daemon}d.py stop"
    # kill off any rogue daemons by the same name (it happens sometimes)
    if [   $(pgrep -fc "ups${daemon}d.py") -ne 0 ]; then
      kill $(pgrep -f  "ups${daemon}d.py")
    fi
    # log the activity
    logger -p user.err -t upsdiagd "  * Daemon ${daemon} stopped."
    # force rm the .pid file
    rm -f "/tmp/upsdiagd/${daemon}.pid"
  done
popd

echo
echo "To re-start all daemons, use:"
echo "./update.sh"
