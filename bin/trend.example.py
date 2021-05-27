#!/usr/bin/env python3

"""Create trendbargraphs for various periods of data."""

import argparse
import configparser
import os
import sqlite3
import warnings

from datetime import datetime as dt

import acgraphlib as alib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# runlist id for daemon :
MYID = 'DEFAULT'
# app_name :
HERE = os.path.realpath(__file__).split('/')
MYAPP = HERE[-3]
MYROOT = "/".join(HERE[0:-3])
NODE = os.uname()[1]
ROOM_ID = NODE[-2:]

iniconf = configparser.ConfigParser()
iniconf.read(f"{MYROOT}/{MYAPP}/config.ini")
DATABASE = iniconf.get(MYID, 'databasefile').replace('__', ROOM_ID)
DATABASE = f'{MYROOT}/{DATABASE}'


def fetch_last_days(hours_to_fetch):
    """
    ...
    """
    global DATABASE
    where_condition = f" (sample_time >= datetime(\'now\', \'-{hours_to_fetch + 1} hours\'))"
    with sqlite3.connect(DATABASE) as con:
        df = pd.read_sql_query(f"SELECT * FROM aircon WHERE {where_condition}",
                            con,
                            parse_dates='sample_time',
                            index_col='sample_epoch')
    # convert the data
    for c in df.columns:
        if c not in ['sample_time']:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # df.drop('sample_time', axis=1)
    df.index = pd.to_datetime(df.index, unit='s').tz_localize("UTC").tz_convert("Europe/Amsterdam")
    # resample to monotonic timeline
    df = df.resample('2min').mean()
    df = df.interpolate(method='slinear')
    df = df.reset_index(level=['sample_epoch'])
    # remove NaNs
    for idx, tmpr in enumerate(df['temperature_th']):
        if np.isnan(tmpr):
            df.at[idx, 'temperature_th'] = df.at[idx, 'temperature_sht']
    # remove NaNs
    for idx, hum in enumerate(df['humidity_th']):
        if np.isnan(hum):
            df.at[idx, 'humidity_th'] = df.at[idx, 'humidity_sht']

    # calculate moisture
    df['moisture'] = alib.moisture(df['temperature_th'], df['humidity_th'], df['pressure'])
    # calculate delta_T
    df['delta_t'] = np.array(df['temperature_outside'] - df['temperature_ac'])

    return df


def y_ax_limits(data_set, accuracy):
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

    """
    # ###############################
    # Create a line plot of temperatures
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['temperature_target',
                             'temperature_ac',
                             'temperature_th',
                             'temperature_bmp',
                             'temperature_sht'
                             ],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['k-','k-','r-','g-', 'b-']
                        )
    # linewidths need to be set separately
    line_widths = [4, 1, 1, 1, 1]
    # alpha needs to be set separately
    alphas = [ahpla/2, ahpla, ahpla, ahpla, ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alphas[i], linewidth=line_widths[i])
    ax1.set_ylabel("[degC]")
    ax1.legend(loc='upper left',
               framealpha=0.2,
               labels=['target', 'AC', 'TEMPerHUM', 'bmp085', 'sht031']
               )
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major',
             axis='y',
             color='k',
             linestyle='--',
             linewidth=0.5
             )
    plt.title(f'{plot_title}')
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}TH.png', format='png')

    """
    # ###############################
    # Create a line plot of outside temperature
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['temperature_outside', 'delta_t'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['k-', 'r-'],
                          secondary_y=['delta_t']
                          )
    lws = [2]
    lwsr = [1]
    alp = [ahpla]
    alpr = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    for i, l in enumerate(ax1.right_ax.lines):
        plt.setp(l, alpha=alpr[i], linewidth=lwsr[i])
    y_hi = np.ceil(np.nanmax(data_frame['temperature_outside']) / 2) * 2
    y_lo = np.floor(np.nanmin(data_frame['temperature_outside']) / 2) * 2
    ax1.set_ylim(y_ax_limits(data_frame['temperature_outside'], 2))
    y_hi = np.ceil(np.nanmax(data_frame['delta_t']) / 2) * 2
    y_lo = np.floor(np.nanmin(data_frame['delta_t']) / 2) * 2
    ax1.right_ax.set_ylim(y_ax_limits(data_frame['delta_t'], 2))
    ax1.set_ylabel("[degC]")
    ax1.right_ax.set_ylabel("[K]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['outside'])
    ax1.right_ax.legend(loc='upper right', framealpha=0.2, labels=['deltaT'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}dT.png', format='png')

    """
    # ###############################
    # Create a line plot of humidities & moisture content
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['humidity_th', 'humidity_sht', 'moisture'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['b-','b--','r-'],
                          secondary_y=['moisture']
                          )
    lws = [1, 1]
    lwsr = [1]
    alp = [ahpla, ahpla]
    alpr = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    for i, l in enumerate(ax1.right_ax.lines):
        plt.setp(l, alpha=alpr[i], linewidth=lwsr[i])
    # print("limits:", y_ax_limits(data_frame['humidity_th'], 10))
    y_lo = np.floor(np.nanmin(data_frame['humidity_th']) / 10) * 10
    if np.isnan(y_lo):
        y_lo = 0
    y_hi = np.ceil(np.nanmax(data_frame['humidity_th']) / 10) * 10
    if np.isnan(y_hi):
        y_hi = y_lo + 1
    ax1.set_ylim(y_ax_limits(data_frame['humidity_th'], 10))
    # ax1.set_ylim([y_lo,y_hi])
    y_hi = np.ceil(np.nanmax(data_frame['moisture']) / 2) * 2
    y_lo = np.floor(np.nanmin(data_frame['moisture']) / 2) * 2
    ax1.right_ax.set_ylim(y_ax_limits(data_frame['moisture'], 2))
    #ax1.right_ax.set_ylim([y_lo,y_hi])
    ax1.set_ylabel("[%]")
    ax1.right_ax.set_ylabel("[g/m3]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['TEMPerHUM', 'sht031'])
    ax1.right_ax.legend(loc='upper right', framealpha=0.2, labels=['Moisture'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}M.png', format='png')

    """
    # ###############################
    # Create a line plot of pressure
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['pressure'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['g']
                          )
    lws = [4]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    y_hi = np.ceil(np.nanmax(data_frame['pressure']) / 10) * 10
    y_lo = np.floor(np.nanmin(data_frame['pressure']) /10) * 10
    ax1.set_ylim(y_ax_limits(data_frame['pressure'], 10))
    ax1.set_ylabel("[mbara]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['bmp085'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}P.png', format='png')

    """
    # ###############################
    # Create a line plot of CO2
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['co2'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['brown']
                          )
    lws = [4]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    y_hi = np.ceil(np.nanmax(data_frame['co2']) / 1000) * 1000
    y_lo = np.floor(np.nanmin(data_frame['co2']) /1000) * 1000
    ax1.set_ylim(y_ax_limits(data_frame['co2'], 1000))
    ax1.set_ylabel("[ppm]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['eCO2'])
    # ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}CO2.png', format='png')

    """
    # ###############################
    # Create a line plot of total VOC
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['voc'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['magenta']
                          )
    lws = [4]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    y_hi = np.ceil(np.nanmax(data_frame['voc']) / 100) * 100
    y_lo = np.floor(np.nanmin(data_frame['voc']) /100) * 100
    ax1.set_ylim(y_ax_limits(data_frame['voc'], 100))
    ax1.set_ylabel("[ppb]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['TVOC'])
    ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}VOC.png', format='png')

    """
    # ###############################
    # Create a line plot of compressor freq
    # ###############################
    """
    plt.rc('font', size=fig_fontsize)
    ax1 = data_frame.plot(x='sample_epoch',
                          y=['cmp_freq'],
                          kind='line',
                          figsize=(fig_x, fig_y),
                          style=['grey']
                          )
    lws = [2]
    alp = [ahpla]
    for i, l in enumerate(ax1.lines):
        plt.setp(l, alpha=alp[i], linewidth=lws[i])
    ax1.set_ylabel("[-]")
    ax1.legend(loc='upper left', framealpha=0.2, labels=['compressor freq'])
    ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    # plt.tight_layout()
    plt.savefig(fname=f'{output_file}F.png', format='png')

def main():
    """
      This is the main loop
      """
    global MYAPP
    global OPTION
    if OPTION.hours:
        plot_graph(f'/tmp/{MYAPP}/site/img/pastday_',
                   fetch_last_days(OPTION.hours),
                   f"Trend afgelopen dagen ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
                   )
    # if OPTION.days:
    #     plot_graph(f'/tmp/{MYAPP}/site/img/pastmonth_',
    #                fetch_last_month(OPTION.days),
    #                f"Trend afgelopen maand ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
    #                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a trendgraph")
    parser.add_argument('-hr', '--hours', type=int, help='create an hour-trend of <HOURS> ')
    parser.add_argument('-d', '--days', type=int, help='create a day-trend of <DAYS>')
    OPTION = parser.parse_args()
    if OPTION.hours == 0:
        OPTION.hours = 50
    if OPTION.days == 0:
        OPTION.days = 50
    main()
