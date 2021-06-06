#!/usr/bin/env python3

"""Create trendbargraphs for various periods of data."""

import argparse
import configparser
import os
import sqlite3
import warnings

from datetime import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# app_name :
HERE = os.path.realpath(__file__).split('/')
# runlist id for daemon :
MYID = HERE[-1]
MYAPP = HERE[-3]
MYROOT = "/".join(HERE[0:-3])
NODE = os.uname()[1]

# example values:
# HERE: ['', 'home', 'pi', 'upsdiagd', 'bin', 'ups.py']

iniconf = configparser.ConfigParser()
iniconf.read(f"{MYROOT}/{MYAPP}/config.ini")
DATABASE = iniconf.get('DEFAULT', 'databasefile')
if DATABASE[0] not in ['/']:
    # path is relative
    DATABASE = f'{MYROOT}/{DATABASE}'


def fetch_last_day(hours_to_fetch):
    """
    ...
    """
    global DATABASE
    where_condition = f" (sample_time >= datetime(\'now\', \'-{hours_to_fetch + 1} hours\'))"
    with sqlite3.connect(DATABASE) as con:
        df = pd.read_sql_query(f"SELECT * FROM ups WHERE {where_condition}",
                            con,
                            parse_dates='sample_time',
                            index_col='sample_epoch')
    # convert the data
    for c in df.columns:
        if c not in ['sample_time']:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df.index = pd.to_datetime(df.index, unit='s').tz_localize("UTC").tz_convert("Europe/Amsterdam")
    # resample to monotonic timeline
    df = df.resample('2min').mean()
    df = df.interpolate(method='slinear')
    df = df.reset_index(level=['sample_epoch'])
    return df


def y_ax_limits(data_set, accuracy):
    """Determine proper y-axis scaling

    Args:
        data_set (a single dataframe row): containing the data
        accuracy (int): round the y-limit up or down to the closest multiple of this parameter

    Returns:
        list: [lower limit, upper limit] as calculated
    """
    hi_limit = np.ceil(np.nanmax(data_set) / accuracy) * accuracy
    lo_limit = np.floor(np.nanmin(data_set) / accuracy) * accuracy
    if np.isnan(lo_limit):
        lo_limit = 0
    if np.isnan(hi_limit):
        hi_limit = lo_limit + accuracy
    return [lo_limit, hi_limit]


def plot_graph(output_file, data_frame, plot_title):
    """
    Create graphs
    """

    # Set the bar width
    # bar_width = 0.75
    fig_x = 10
    fig_y = 2.5
    fig_fontsize = 6.5
    ahpla = 0.6

    # ###############################
    # Create a line plot of load and line voltage
    # ###############################
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['load_ups', 'volt_in'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['b-', 'r-'],
                          secondary_y=['volt_in']
                          )
    lws = [1]
    lwsr = [1]
    alp = [ahpla]
    alpr = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    for i, l in enumerate(ax1.right_ax.lines):
        plt.setp(l, alpha=alpr[i], linewidth=lwsr[i])
    ax1.set_ylim(y_ax_limits(data_frame['load_ups'], 0.5))
    ax1.right_ax.set_ylim(y_ax_limits(data_frame['volt_in'], 20))
    ax1.set_ylabel("[%]")
    ax1.right_ax.set_ylabel("[V]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['load'])
    ax1.right_ax.legend(loc='upper right', framealpha=0.2, labels=['line'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    plt.title(f'{plot_title}')
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}V.png', format='png')

    # ###############################
    # Create a line plot of runtime
    # ###############################
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['runtime_bat'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['g']
                          )
    lws = [4]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    ax1.set_ylim(y_ax_limits(data_frame['runtime_bat'], 50))
    ax1.set_ylabel("[sec]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['runtime'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}RUN.png', format='png')

    # ###############################
    # Create a line plot of charge
    # ###############################
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['charge_bat'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['brown']
                          )
    lws = [4]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    ax1.set_ylim(y_ax_limits(data_frame['charge_bat'], 50))
    ax1.set_ylabel("[%]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['charge'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}CHG.png', format='png')



def main():
    """
      This is the main loop
      """
    global MYAPP
    global OPTION
    if OPTION.hours:
        plot_graph(f'/tmp/{MYAPP}/site/img/pastday_',
                   fetch_last_day(OPTION.hours),
                   f"Trend afgelopen uren ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
                   )
    if OPTION.days:
        plot_graph(f'/tmp/{MYAPP}/site/img/pastmonth_',
                   fetch_last_day(OPTION.days * 24),
                   f"Trend afgelopen dagen ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
                   )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a trendgraph")
    parser.add_argument('-hr', '--hours', type=int, help='create an hour-trend of <HOURS>')
    parser.add_argument('-d', '--days', type=int, help='create a day-trend of <DAYS>')
    OPTION = parser.parse_args()
    if OPTION.hours == 0:
        OPTION.hours = 50
    if OPTION.days == 0:
        OPTION.days = 50
    main()
