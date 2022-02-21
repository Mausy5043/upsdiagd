# UPSDIAGD

Scripts are supplied that allow you to 
* interrogate a `usbhid-ups` compliant UPS
* store specific data in a sqlite3 database (server not included; you'll need to set-up your own)
* query the (not included) sqlite3 database for interesting data
* plot some graphs
* push graphs to a website (webserver not included; you'll need to set-up your own)

## Installing

```
sudo su -
cd /path/to/where/you/want/store/upsdiagd
git clone https://github.com/Mausy5043/upsdiagd.git
cd upsdiagd
./install.sh
./update.sh
```

## Additional software:
This repo assumes you have already installed and configured `nut`.  

## Hardware:
Raspberry Pi 1B or better, connected to a UPS via USB cable.

Known to work with:
- APC Back-UPS 700 (BE-700GR)
- EATON ProtectionStation 650

(probably all UPSes that support the `usbhid-ups` driver)
