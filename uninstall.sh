#!/bin/bash

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)

pushd "${HERE}" || exit 1
    # shellcheck disable=SC1091
    source ./bin/constants.sh

    echo
    echo -n "Started UNinstalling ${app_name} on "
    date
    echo

    # allow user to abort
    sleep 10

    ./stop.sh

    sudo systemctl disable upsdiag.fles.service &
    sudo systemctl disable upsdiag.ups.service &

    sudo systemctl disable upsdiag.trend.day.timer &
    sudo systemctl disable upsdiag.update.timer &
    wait

popd || exit

echo
echo "*********************************************************"
echo -n "Finished UNinstallation of ${app_name} on "
date
echo
