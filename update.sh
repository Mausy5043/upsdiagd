#!/bin/bash

# update.sh is run periodically by a service.
# * It synchronises the local copy of ${app_name} with the current GitLab branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

logger "Started upsdiag update."

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)


pushd "${HERE}" || exit 1
    # sudo systemctl stop fles.service

    # shellcheck disable=SC1091
    source ./bin/constants.sh

    website_dir="/tmp/${app_name}/site"
    website_image_dir="${website_dir}/img"

    # shellcheck disable=SC2154
    branch=$(<"${HOME}/.${app_name}.branch")

    # make sure working tree exists
    if [ ! -d "${website_image_dir}" ]; then
        mkdir -p "${website_image_dir}"
        chmod -R 755 "/tmp/${app_name}"
    fi

    git fetch origin || sleep 60; git fetch origin
    # Check which files have changed
    DIFFLIST=$(git --no-pager diff --name-only "${branch}..origin/${branch}")
    git pull
    git fetch origin
    git checkout "${branch}"
    git reset --hard "origin/${branch}" && git clean -f -d
    chmod -x ./services/*

    sudo systemctl stop upsdiag.fles.service &
    sudo systemctl stop upsdiag.ups.service &
    sudo systemctl stop upsdiag.trend.day.timer &
    echo "Please wait while services stop..."; wait

    changed_config=0
    changed_service=0
    changed_daemon=0
    changed_lib=0
    for fname in $DIFFLIST; do
        if [[ "${fname}" == "config.ini" ]]; then
            changed_config=1
        fi
        if [[ "${fname:0:9}" == "services/" ]]; then
            changed_service=1
        fi
        if [[ "${fname}" == "bin/ups.py" ]]; then
           changed_daemon=1
        fi
        if [[ "${fname:${#fname}-6}" == "lib.py" ]]; then
            changed_lib=1
        fi
    done

    if [[ changed_service -eq 1 ]] || [[ changed_lib -eq 1 ]]; then
        echo "  ! Service or timer changed"
        echo "  o Reinstalling services"
        sudo cp ./services/*.service /etc/systemd/system/
        echo "  o Reinstalling timers"
        sudo cp ./services/*.timer /etc/systemd/system/
        sudo systemctl daemon-reload
    fi

    if [ ! "${1}" == "--systemd" ]; then
        echo "Skipping graph creation"
    else
        echo "Creating graphs [1]"
        bin/pastday.sh
        echo "Creating graphs [2]"
        bin/pastmonth.sh
    fi

    sudo systemctl start upsdiag.fles.service &
    sudo systemctl start upsdiag.ups.service &
    sudo systemctl start upsdiag.trend.day.timer &
    echo "Please wait while services start..."; wait

    cp "./www/index.html" "${website_dir}"
    cp "./www/favicon.ico" "${website_dir}"

popd || exit

logger "Finished upsdiag update."
