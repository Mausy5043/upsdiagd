# UPSDIAGD

Scripts are supplied that allow you to 
* interrogate a `usbhid-ups` compliant UPS
* store specific data in a MySQL database (server not included; you'll need to set-up your own)
* query the (not included) MySQL database for interesting data
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
For an example of the, please refer to [these files](https://github.com/Mausy5043/raspboot/tree/master/rbups)

## Hardware:
Raspberry Pi 1B connected to a UPS via USB cable.

Known to work with:
- APC Back-UPS 700 (BE-700GR)
- EATON ProtectionStation 650

(probably all UPSes that support the `usbhid-ups` driver)

## Attribution
The python code for the daemons is based on previous work by
- [Charles Menguy](http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
- [Sander Marechal](http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)
