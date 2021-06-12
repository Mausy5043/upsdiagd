#!/usr/bin/env python3
"""Common functions for Flask webUI"""

import configparser
import json
import os
import sqlite3
import time


def initial_state():
    """
    Set the factory settings for the application.
    The settings are stored in a dictionary.
    """
    defstate = dict()
    """OPERATOR :
       -1 : MANUAL control; user directly controls the airco; the app does nothing.
        0 : SEMI-AUTO control; user controls the airco via the application
        1 : AUTO;
        2 : REMOTE control; the application is in control of the airco

        MODE_SP :
       -1 : OFF
        0 : AUTO
        1 : COOL
        2 : DRY
        3 : HEAT
        4 : FAN ONLY
    """
    return defstate


class Fles:
    def __init__(self):
        # app info :
        # path to this file as a list of elements
        self.HERE = os.path.realpath(__file__).split('/')
        self.MYLEVEL = 4  # aircon =1, bin =2, fles =3
        # element that contains the appname (given the location of this file)
        self.MYAPP = self.HERE[-self.MYLEVEL]
        # absolute path to the app's root
        self.MYROOT = "/".join(self.HERE[0:-self.MYLEVEL])
        self.NODE = os.uname()[1]  # name of the host
        self.ROOM_ID = self.NODE[-2:]  # inferred room-id

        iniconf = configparser.ConfigParser()
        iniconf.read(f"{self.MYROOT}/{self.MYAPP}/config.ini")
        DATABASE = iniconf.get('DEFAULT', 'databasefile')
        self.DATABASE = f'{self.MYROOT}/{DATABASE}'
        self.CONFIG = f'{self.MYROOT}/.config/upsdata.json'
        self.req_state = dict()
        self.ctrl_state = dict()
        self.load_state()

    def get_latest_data(self, fields):
        """Retrieve the most recent datapoints from the database."""
        db_con = sqlite3.connect(self.DATABASE)
        with db_con:
            db_cur = db_con.cursor()
            db_cur.execute(f"SELECT {fields} FROM ups \
                             WHERE sample_epoch = (SELECT MAX(sample_epoch) FROM ups) \
                             ;")
            db_data = db_cur.fetchall()
        return list(db_data[0])

    def set(self, key, value):
        """Store the key-value pair"""
        self.req_state[key] = value
        # immediately save the new state
        self.save_state()

    def get(self, key):
        """Return the value of the key"""
        #  Loading the state every time a parameter is needed
        #  might enable adjusting settings via the terminal
        #  on the fly.
        self.load_state()
        return self.req_state[key]

    def get_ctrl(self, key):
        """Return the value of the key"""
        #  Loading the state every time a parameter is needed
        #  might enable adjusting settings via the terminal
        #  on the fly.
        self.load_state()
        return self.ctrl_state[key]

    def get_ctrl_state(self):
        self.load_state()
        return self.ctrl_state

    def save_state(self):
        """Save the settings to disk."""
        nosj_data = dict()
        if os.path.isfile(self.CONFIG):
            with open(self.CONFIG, 'r') as fp:
                nosj_data = json.load(fp)
        nosj_data['request'] = self.req_state
        # update the timestamp
        nosj_data['time'] = time.time()
        with open(self.CONFIG, 'w') as fp:
            json.dump(nosj_data, fp, sort_keys=True, indent=4)

    def load_state(self):
        """Load the factory settings, then combine them
        with a local configurationfile (if exists)."""
        nosj_data = dict()
        defaults = initial_state()
        if os.path.isfile(self.CONFIG):
            with open(self.CONFIG, 'r') as fp:
                nosj_data = json.load(fp)
                try:
                    self.req_state = nosj_data['request']
                except KeyError:
                    nosj_data['request'] = {}
                    pass
                try:
                    self.ctrl_state = nosj_data['control']
                except KeyError:
                    nosj_data['control'] = {}
                    pass
        # add missing defaults
        for element in defaults:
            if element not in self.req_state:
                self.req_state[element] = defaults[element]
