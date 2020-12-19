#!/bin/bash

# this repo gets installed either manually by the user or automatically by
# a `*boot` repo.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

ME=$(whoami)
HOST=$(hostname)
DB_DIR="${HOME}/bin/.config/database/${HOST}"

required_commonlibversion="0.5.4"
commonlibbranch="v0_5"

echo -n "Started installing UPSDIAGd on "; date
minit=$(echo $RANDOM/555 |bc)
echo "MINIT = $minit"

install_package() {
  # See if packages are installed and install them.
  package=$1
  echo "*********************************************************"
  echo "* Requesting ${package}"
  status=$(dpkg-query -W -f='${Status} ${Version}\n' "${package}" 2>/dev/null | wc -l)
  if [ "${status}" -eq 0 ]; then
    echo "* Installing ${package}"
    echo "*********************************************************"
    sudo apt-get -yuV install "${package}"
  else
    echo "* Already installed !!!"
    echo "*********************************************************"
  fi
}

getfilefromserver() {
  # retrieve files from the network server
  file="${1}"
  mode="${2}"
  cp -rvf  "$HOME/bin/.config/home/${file}" "$HOME/"
  chmod    "${mode}" "$HOME/${file}"
}

sudo apt-get update
# LFTP package
install_package "lftp"

# Python 3 package and associates
install_package "python3"
install_package "build-essential"
install_package "python3-dev"
install_package "python3-pip"

# gnuplot packages
install_package "gnuplot"
install_package "gnuplot-nox"

# sqlite3 support (python3)
install_package "sqlite3"

# Python requirements
python3 -m pip install --upgrade pip setuptools wheel
sudo pip3 install -r requirements.txt

getfilefromserver ".my.ups.cnf" "0740"

commonlibversion=$(pip3 freeze |grep mausy5043 |cut -c 26-)
if [ "${commonlibversion}" != "${required_commonlibversion}" ]; then
  echo "Install common python functions..."
  sudo pip3 uninstall -y mausy5043-common-python
  pushd /tmp || exit 1
    git clone -b "${commonlibbranch}" https://gitlab.com/mausy5043-installer/mausy5043-common-python.git
    pushd /tmp/mausy5043-common-python || exit 1
      sudo ./setup.py install
    # shellcheck disable=SC2164
    popd
    sudo rm -rf mausy5043-common-python/
  # shellcheck disable=SC2164
  popd
  echo
  echo -n "Installed: "
  pip3 freeze | grep mausy5043
  echo
fi

if [ ! -f "${DB_DIR}" ]; then
  echo "Database not found. Creating..."

fi

pushd "${SCRIPT_DIR}" || exit 1
  # To suppress git detecting changes by chmod:
  git config core.fileMode false
  # set the branch
  if [ ! -e "$HOME/.upsdiagd.branch" ]; then
    echo "sqlite3" > "$HOME/.upsdiagd.branch"
  fi

  # Create the /etc/cron.d directory if it doesn't exist
  sudo mkdir -p /etc/cron.d
  # Set up some cronjobs
  echo "# m h dom mon dow user  command" | sudo tee /etc/cron.d/upsdiagd
  echo "$minit  * *   *   *   $ME    $SCRIPT_DIR/update.sh 2>&1 | logger -p info -t upsdiagd" | sudo tee --append /etc/cron.d/upsdiagd
  # @reboot we allow for 10s for the network to come up:
  echo "@reboot               $ME    sleep 10; $SCRIPT_DIR/update.sh 2>&1 | logger -p info -t upsdiagd" | sudo tee --append /etc/cron.d/upsdiagd
# shellcheck disable=SC2164
popd

echo -n "Finished installation of upsdiagd on "; date
