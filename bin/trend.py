#!/usr/bin/env python3

"""Create trendbargraphs for various periods of data."""

import argparse
import configparser
import os
from datetime import datetime as dt

import acgraphlib as alib  # noqa
import matplotlib.pyplot as plt

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


def fetch_last_day(hours_to_fetch):
    """
    ...
    """
    global DATABASE
    config = alib.add_time_line({'grouping': '%m-%d %Hh',
                                 'period': hours_to_fetch,
                                 'timeframe': 'hour',
                                 'database': DATABASE,
                                 'table': 'aircon'
                                 })
    temperature, data_lbls = alib.get_historic_data(config, parameter='temperature')
    temperature_ac, data_lbls = alib.get_historic_data(config, parameter='temperature_ac')
    pressure, data_lbls = alib.get_historic_data(config, parameter='pressure')
    humidity, data_lbls = alib.get_historic_data(config, parameter='humidity')
    totalvoc, data_lbls = alib.get_historic_data(config, parameter='voc')
    co2_conc, data_lbls = alib.get_historic_data(config, parameter='co2')
    cmp_freq, data_lbls = alib.get_historic_data(config, parameter='cmp_freq', somma=True, interp=False)
    return data_lbls, temperature, pressure, humidity, totalvoc, co2_conc, temperature_ac, cmp_freq


def fetch_last_month(days_to_fetch):
    """
    ...
    """
    global DATABASE
    config = alib.add_time_line({'grouping': '%m-%d',
                                 'period': days_to_fetch,
                                 'timeframe': 'day',
                                 'database': DATABASE,
                                 'table': 'aircon'
                                 })
    temperature, data_lbls = alib.get_historic_data(config, parameter='temperature')
    temperature_ac, data_lbls = alib.get_historic_data(config, parameter='temperature_ac')
    pressure, data_lbls = alib.get_historic_data(config, parameter='pressure')
    humidity, data_lbls = alib.get_historic_data(config, parameter='humidity')
    totalvoc, data_lbls = alib.get_historic_data(config, parameter='voc')
    co2_conc, data_lbls = alib.get_historic_data(config, parameter='co2')
    cmp_freq, data_lbls = alib.get_historic_data(config, parameter='cmp_freq', somma=True, interp=False)
    return data_lbls, temperature, pressure, humidity, totalvoc, co2_conc, temperature_ac, cmp_freq


def plot_graph(output_file, data_tuple, plot_title):
    """
    Create graphs
    """
    data_lbls = data_tuple[0]
    temperature = data_tuple[1][:, 0]
    temperature_min = data_tuple[1][:, 1]
    temperature_max = data_tuple[1][:, 2]
    pressure = data_tuple[2][:, 0]
    pressure_min = data_tuple[2][:, 1]
    pressure_max = data_tuple[2][:, 2]
    humidity = data_tuple[3][:, 0]
    humidity_min = data_tuple[3][:, 1]
    humidity_max = data_tuple[3][:, 2]
    tvoc = data_tuple[4][:, 0]
    tvoc_min = data_tuple[4][:, 1]
    tvoc_max = data_tuple[4][:, 2]
    co2c = data_tuple[5][:, 0]
    co2c_min = data_tuple[5][:, 1]
    co2c_max = data_tuple[5][:, 2]
    temperature_ac = data_tuple[6][:, 0]
    # temperature_ac_min = data_tuple[6][:, 1]
    # temperature_ac_max = data_tuple[6][:, 2]
    cmp_freq = data_tuple[7][:, 0]

    moist = alib.moisture(temperature, humidity, pressure) * 1000

    """
    --- Start debugging:
    np.set_printoptions(precision=3)
    print("data_lbls   : ", np.size(data_lbls), data_lbls[-5:])
    print(" ")
    print("temperatuur : ", np.size(temperature), temperature[-5:])
    print("vochtigheid : ", np.size(humidity), humidity[-5:])
    print("vochtgehalte: ", np.size(moist), moist[-5:])
    print(" ")
    print("luchtdruk   : ", np.size(pressure), pressure[-5:])
    print(" ")
    print("Total VOC   : ", np.size(tvoc), tvoc[-5:])
    print("CO2 concen. : ", np.size(co2c), co2c[-5:])
    print("Compressor  : ", np.size(cmp_freq), cmp_freq[-5:])
    --- End debugging.
    """
    # Set the bar width
    bar_width = 0.75
    # positions of the left bar-boundaries
    tick_pos = list(range(1, len(data_lbls) + 1))
    fig_x = 10
    fig_y = 2.5
    fig_fontsize = 6.5

    # *** TEMPERATURE / HUMIDITY
    plt.rc('font', size=fig_fontsize)
    dummy, ax1 = plt.subplots(1, figsize=(fig_x, fig_y))

    """
    # ###############################
    # Create a line plot of temperature/humidity
    # ###############################
    """

    # humidity
    ahpla = 0.4
    ax1.errorbar(tick_pos, humidity,
                 yerr=[humidity - humidity_min, humidity_max - humidity],
                 elinewidth=10,
                 label='Vochtigheid',
                 alpha=ahpla,
                 color='blue',
                 marker='o'
                 )
    ax1.set_ylabel("[%]")
    ax1.legend(loc='upper left', framealpha=0.2)
    y_lo = int(min(humidity) / 5) * 5
    y_hi = int(max(humidity) / 5) * 5 + 5
    if y_lo > 45:
        y_lo = 45
    if y_hi < 55:
        y_hi = 55
    ax1.set_ylim([y_lo, y_hi])

    # Set general plotting stuff
    ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    plt.xticks(tick_pos, data_lbls, rotation=-60)

    ax2 = ax1.twinx()

    # temperature
    ahpla = 0.7
    ax2.errorbar(tick_pos, temperature,
                 yerr=[temperature - temperature_min, temperature_max - temperature],
                 elinewidth=5,
                 label='Temperatuur',
                 alpha=ahpla,
                 color='red',
                 marker='o'
                 )
    ax2.plot(tick_pos, temperature_ac,
             label='Temperatuur (AC)',
             alpha=ahpla,
             color='black',
             marker='.'
             )
    ax2.set_ylabel("[degC]")
    ax2.legend(loc='upper right', framealpha=0.2)
    y_lo = min(int(min(temperature)) - 1, int(min(temperature_ac)) - 1)
    y_hi = max(int(max(temperature)) + 1, int(max(temperature_ac)) + 1)
    if y_lo > 19:
        y_lo = 19
    if y_hi < 22:
        y_hi = 22
    ax2.set_ylim([y_lo, y_hi])

    # Fit every nicely
    plt.title(f'{plot_title}')
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}TH.png', format='png')

    # *** PRESSURE
    plt.rc('font', size=fig_fontsize)
    dummy, ax3 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of pressure
    # ###############################
    """
    ax3.bar(tick_pos, pressure_min,
            width=bar_width,
            label='Pressure (min)',
            alpha=ahpla,
            color='lightgreen',
            align='center',
            bottom=0
            )
    ax3.bar(tick_pos, pressure_max - pressure_min,
            width=bar_width,
            label='Pressure (max)',
            alpha=ahpla,
            color='green',
            align='center',
            bottom=pressure_min
            )

    # Set Axes stuff
    ax3.set_ylabel("[mbara]")
    ax3.set_xlabel("Datetime")
    ax3.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax3.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    y_lo = min(pressure_min) - 2
    y_hi = max(pressure_max) + 2
    if y_lo > 990:
        y_lo = 990
    if y_hi < 1020:
        y_hi = 1020
    ax3.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}P.png', format='png')

    # *** TOTAL VOC
    plt.rc('font', size=fig_fontsize)
    dummy, ax4 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of total VOCs
    # ###############################
    """
    ax4.bar(tick_pos, tvoc_min,
            width=bar_width,
            label='eTVOC (min)',
            alpha=ahpla,
            color='magenta',
            align='center',
            bottom=0
            )
    ax4.bar(tick_pos, tvoc_max - tvoc_min,
            width=bar_width,
            label='eTVOC (max)',
            alpha=ahpla,
            color='purple',
            align='center',
            bottom=tvoc_min
            )

    # Set Axes stuff
    ax4.set_ylabel("eTVOC [ppb]")
    ax4.set_xlabel("Datetime")
    ax4.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax4.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    y_lo = min(tvoc) - 10
    y_hi = max(tvoc) + 10
    if y_lo > 0:
        y_lo = 0
    if y_hi < 1000:
        y_hi = int(y_hi / 100) * 100 + 100
    ax4.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}VOC.png', format='png')

    # *** CO2 CONCENTRATION
    plt.rc('font', size=fig_fontsize)
    dummy, ax5 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of CO2 concentration
    # ###############################
    """
    ax5.bar(tick_pos, co2c_min,
            width=bar_width,
            label='eCO2 (min)',
            alpha=ahpla,
            color='sandybrown',
            align='center',
            bottom=0
            )
    ax5.bar(tick_pos, co2c_max - co2c_min,
            width=bar_width,
            label='eCO2 (max)',
            alpha=ahpla,
            color='saddlebrown',
            align='center',
            bottom=co2c_min
            )

    # Set Axes stuff
    ax5.set_ylabel("eCO2 [ppm]")
    ax5.set_xlabel("Datetime")
    ax5.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax5.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    y_lo = min(co2c) - 10
    y_hi = max(co2c) + 10
    if y_lo > 0:
        y_lo = 0
    if y_hi < 5000:
        y_hi = int(y_hi / 100) * 100 + 100
    ax5.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}CO2.png', format='png')

    # *** MOISTURE
    ahpla = 0.4
    plt.rc('font', size=fig_fontsize)
    dummy, ax6 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of moisture
    # ###############################
    """
    ax6.bar(tick_pos, moist,
            width=bar_width,
            label='Moisture',
            alpha=ahpla,
            color='blue',
            align='center',
            bottom=0
            )

    # Set Axes stuff
    ax6.set_ylabel("[g water/m3 lucht]")
    ax6.set_xlabel("Datetime")
    ax6.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax6.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    y_lo = min(moist) - 0.2
    y_hi = max(moist) + 0.2
    if y_lo > 4.0:
        y_lo = 4.0
    if y_hi < 10.0:
        y_hi = 10.0
    ax6.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}M.png', format='png')

    # *** CMP_FREQ
    ahpla = 0.8
    plt.rc('font', size=fig_fontsize)
    dummy, ax7 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of compressor frequency
    # ###############################
    """
    ax7.bar(tick_pos, cmp_freq,
            width=bar_width,
            label='Compressor',
            alpha=ahpla,
            color='grey',
            align='center',
            bottom=0
            )

    # Set Axes stuff
    ax7.set_ylabel("[freq]")
    ax7.set_xlabel("Datetime")
    ax7.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax7.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    # ax7.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}F.png', format='png')


def main():
    """
      This is the main loop
      """
    global MYAPP
    global OPTION
    if OPTION.hours:
        plot_graph(f'/tmp/{MYAPP}/site/img/pastday_',
                   fetch_last_day(OPTION.hours),
                   f"Trend afgelopen dagen ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
                   )
    if OPTION.days:
        plot_graph(f'/tmp/{MYAPP}/site/img/pastmonth_',
                   fetch_last_month(OPTION.days),
                   f"Trend afgelopen maand ({dt.now().strftime('%d-%m-%Y %H:%M:%S')})"
                   )


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
