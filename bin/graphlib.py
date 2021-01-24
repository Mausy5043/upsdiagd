#!/usr/bin/env python3

"""Common functions for use by aircon*.py scripts"""

import datetime as dt
import sqlite3 as s3

import numpy as np


def add_time_line(config):
    final_epoch = int(dt.datetime.now().timestamp())
    step_epoch = 10 * 60
    multi = 600
    if config['timeframe'] is 'hour':
        multi = 3600
    if config['timeframe'] is 'day':
        multi = 3600 * 24
    if config['timeframe'] is 'month':
        multi = 3600 * 24 * 31
    if config['timeframe'] is 'year':
        multi = 3600 * 24 * 366
    start_epoch = int((final_epoch - (multi * config['period'])) / step_epoch) * step_epoch
    config['timeline'] = np.arange(start_epoch, final_epoch, step_epoch, dtype='int')
    return config


def get_historic_data(dicti, parameter=None, from_start_of_year=False, include_today=True,
                      somma=False, interp=True, extra_where=''):
    """Fetch historic data from SQLITE3 database.

    :param
    dict: dict - containing settings
    parameter: str - columnname to be collected
    from_start_of_year: boolean - fetch data from start of year or not
    include_today: boolean - also fetch today's data
    somma: boolean - return sum of grouped data (True) OR return avg of grouped data (False; default)

    :returns
    ret_data: numpy list int - data returned
    ret_lbls: numpy list str - label texts returned
    """
    period = dicti['period']
    if from_start_of_year:
        interval = f"datetime(datetime(\'now\', \'-{period + 1} {dicti['timeframe']}\'), \'start of year\')"
    else:
        interval = f"datetime(\'now\', \'-{period + 1} {dicti['timeframe']}\')"
    if include_today:
        and_where_not_today = ''
    else:
        and_where_not_today = 'AND (sample_time <= datetime(\'now\', \'-1 day\'))'
    filter_where = ''
    if extra_where:
        filter_where = ''.join([' AND ', extra_where])

    db_con = s3.connect(dicti['database'])
    with db_con:
        db_cur = db_con.cursor()
        db_cur.execute(f"SELECT sample_epoch, "
                       f"{parameter} "
                       f"FROM {dicti['table']} "
                       f"WHERE (sample_time >= {interval}) "
                       f"  {and_where_not_today} "
                       f"  {filter_where} "
                       f"ORDER BY sample_epoch ASC"
                       f";"
                       )
        db_data = db_cur.fetchall()

    data = np.array(db_data)
    for i, row in enumerate(data):
        for c in row:
            if c is None:
                data = np.delete(data, i, 0)

    if interp:
        # interpolate the data to monotonic 10minute intervals provided by dicti['timeline']
        ret_epoch, ret_intdata = interplate(dicti['timeline'],
                                            np.array(data[:, 0], dtype=int),
                                            np.array(data[:, 1], dtype=int)
                                            )
    else:
        ret_epoch = np.array(data[:, 0], dtype=int)
        ret_intdata = np.array(data[:, 1], dtype=int)

    # group the data by dicti['grouping']
    if dicti['grouping'] is not '':
        ret_lbls, ret_grpdata = fast_group_data(ret_epoch, ret_intdata, dicti['grouping'], somma)
        ret_data = ret_grpdata
    else:
        # return the raw data if no grouping is given
        return np.array(db_data)[:, 1], np.array(db_data)[:, 0]

    return ret_data[-period:], ret_lbls[-period:]


def interplate(epochrng, epoch, data):
    """
    Interpolate any missing datapoints to create a neat
    monotonic dataset with 10 minute intervals
    """
    datarng = np.interp(epochrng, epoch, data)
    return epochrng, datarng


def fast_group_data(x_epochs, y_data, grouping, somma):
    """A faster version of group_data()."""
    # convert y-values to numpy array
    y_data = np.array(y_data)
    # convert epochs to text
    x_texts = np.array([dt.datetime.fromtimestamp(i).strftime(grouping) for i in x_epochs], dtype='str')
    """x_texts = ['12-31 20h' '12-31 21h' '12-31 21h' '12-31 21h' '12-31 21h' '12-31 21h'
                 '12-31 21h' '12-31 22h' '12-31 22h' '12-31 22h' '12-31 22h' '12-31 22h'
                 :
                 '01-01 09h' '01-01 10h' '01-01 10h' '01-01 10h' '01-01 10h' '01-01 10h'
                 '01-01 10h']
    """
    # compress x_texts to a unique list
    # order must be preserved
    _, loc1 = np.unique(x_texts, return_index=True)
    loc1 = np.sort(loc1)
    unique_x_texts = x_texts[loc1]
    # preform the returned y-data array
    y_shape = (np.shape(unique_x_texts)[0], 3)
    returned_y_data = np.zeros(y_shape)

    loc2 = len(x_texts) - 1 - np.unique(np.flip(x_texts), return_index=True)[1]
    loc2 = np.sort(loc2)

    for idx in range(0, len(loc1)):
        y_pnt = y_min = y_max = None
        if loc1[idx] == loc2[idx]:
            data_y = y_data[loc1[idx]]
        else:
            data_y = y_data[loc1[idx]:loc2[idx]]
        if somma:
            y_pnt = np.sum(data_y)
        else:
            y_pnt = np.mean(data_y)
            y_min = np.min(data_y)
            y_max = np.max(data_y)
        returned_y_data[idx] = [y_pnt, y_min, y_max]

    return unique_x_texts, returned_y_data


def moisture(temperature, relative_humidity, pressure):
    kelvin = temperature + 273.15
    pascal = pressure * 100
    rho = (287.04 * kelvin) / pascal

    es = 611.2 * np.exp(17.67 * (kelvin - 273.15) / (kelvin - 29.65))
    rvs = 0.622 * es / (pascal - es)
    rv = relative_humidity / 100. * rvs
    qv = rv / (1 + rv)
    moistair = qv * rho  # kg water per m3 air
    return np.array(moistair)


def wet_bulb_temperature(temperature, relative_humidity):
    wbt = temperature * np.arctan(0.151977 * np.sqrt(relative_humidity + 8.313659)) \
          + np.arctan(temperature + relative_humidity) \
          - np.arctan(relative_humidity - 1.676331) \
          + 0.00391838 * np.power(relative_humidity, 1.5) * np.arctan(0.023101 * relative_humidity) \
          - 4.686035
    return wbt
