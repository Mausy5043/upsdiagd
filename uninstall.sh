#!/bin/bash

# this repo gets installed either manually by the user or automatically by
# a `*boot` repo.

# The hostname is in /etc/hostname prior to running `install.sh` here!
HOSTNAME=$(cat /etc/hostname)

echo -n "Started UNinstalling UPSDIAGd on "; date

pushd "$HOME/upsdiagd" || exit 1
  # shellcheck disable=SC1091
 source ./includes

  # prevent restarts of daemons while the script is still running
  sudo rm /etc/cron.d/upsdiagd

  echo "  Stopping all diagnostic daemons"
  for daemon in $upslist; do
    echo "Stopping "$daemon
    eval "./ups"$daemon"d.py stop"
  done
  echo "  Stopping all service daemons"
  for daemon in $srvclist; do
    echo "Stopping "$daemon
    eval "./ups"$daemon"d.py stop"
  done
popd

echo -n "Finished UNinstallation of upsdiagd on "; date
