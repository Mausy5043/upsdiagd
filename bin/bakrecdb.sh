#!/bin/bash

HERE=$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)

install_database_file() {
    # $1 : path to DB file
    # $2 : DB filename
    # $3 : remote path to DB file
    mkdir -p "${1}"
    recover_database_file "${1}" "${2}" "${3}"
    if [ ! -e "${1}/${2}" ]; then
        create_database_file "idf1" "${1}" "${2}"
    fi
}

backup_database_file() {
    # $1 : path to DB file
    # $2 : DB filename
    # $3 : remote path to DB file
    if [ -e "${1}/${2}" ]; then
        echo "Standby while making a backup of ${2} ..."
        sqlite3 "${1}/${2}" ".backup ${3}/${2}"
    fi
}

recover_database_file() {
    # $1 : path to DB file
    # $2 : DB filename
    # $3 : remote path to DB file
    if [ -e "${3}/${2}" ]; then
        echo "Standby while recovering ${2} from backup ..."
        cp "${3}/${2}" "${1}/${2}"
    fi
}

create_database_file() {
    # $1 : command 'idf1'
    # $2 : path to DB file
    # $3 : DB filename
    # !! WARNING !!
    # Calling this function from the wild will overwrite an existing database!
    #
    case ${1} in
        idf1)
            sqlite3 "${2}/${3}" <table32.sqlite3.sql
            ;;
        *)
            echo "Unsupported functionality. Use the 'install_database_file' function instead!"
            exit 1
            ;;
    esac
}

pushd "${HERE}" >/dev/null || exit 1
    # shellcheck disable=SC1091
    source ../includes
    # check commandline parameters
    for i in "$@"; do
        case $i in
        -i | --install)
            install_database_file "${local_db_path}" "${database_filename}" "${remote_db_path}"
            ;;
        -b | --backup)
            backup_database_file "${local_db_path}" "${database_filename}" "${remote_db_path}"
            ;;
        -r | --recover)
            recover_database_file "${local_db_path}" "${database_filename}" "${remote_db_path}"
            ;;
        *)
            # unknown option
            echo "** Unknown option **"
            echo
            echo "Syntax:"
            echo "bakrecdb.sh [-i|--install] [-b|--backup] [-r|--recover]"
            echo
            exit 1
            ;;
        esac
    done
popd >/dev/null || exit
