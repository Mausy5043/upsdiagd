#!/bin/bash

# Use stop.sh to stop all daemons in one go
# You can use update.sh to get everything started again.

HERE=$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)

pushd "${HERE}" || exit 1
    # shellcheck disable=SC1091
    source ./bin/constants.sh

    sudo systemctl stop upsdiag.fles.service &

    sudo systemctl stop upsdiag.ups.service &

    sudo systemctl stop upsdiag.backupdb.timer &
    sudo systemctl stop upsdiag.trend.day.timer &
    sudo systemctl stop upsdiag.update.timer &
    wait

    ./bin/bakrecdb.sh --backup
popd || exit
