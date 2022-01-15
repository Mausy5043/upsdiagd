#!/bin/bash

# query daily totals for a period of one month

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)

pushd "${HERE}" >/dev/null || exit 1
    # shellcheck disable=SC1091
    source ./constants.sh
    ./trend.py --days 0

    CURRENT_EPOCH=$(date +'%s')
    # do some maintenance
    # shellcheck disable=SC2154
    echo -n "${db_full_path} integrity check: "
    sqlite3 "${db_full_path}" "PRAGMA integrity_check;"
    sqlite3 "${db_full_path}" "REINDEX;"

    # Keep upto 400 days of data
    PURGE_EPOCH=$(echo "${CURRENT_EPOCH} - (400 * 24 * 3600)" |bc)
    sqlite3 "${db_full_path}" \
            "DELETE FROM ups WHERE sample_epoch < ${PURGE_EPOCH};"

popd >/dev/null || exit
