#!/bin/bash

# query daily totals for a period of one month

HERE=$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)

pushd "${HERE}" >/dev/null || exit 1
    # shellcheck disable=SC1091
    source ../includes
    ./trend.py --days 0

    CURRENT_EPOCH=$(date +'%s')
    # Keep upto 180 days of data
    PURGE_EPOCH=$(echo "${CURRENT_EPOCH} - (180 * 24 * 3600)" |bc)
    sqlite3 "${local_db_path}/${database_filename}" \
        "DELETE FROM aircon WHERE sample_epoch < ${PURGE_EPOCH};"

popd >/dev/null || exit
