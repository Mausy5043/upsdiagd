#!/usr/bin/env python3

"""Create trendbargraphs for various periods of data."""

import argparse
import configparser
import os
from datetime import datetime as dt

import graphlib as glib  # noqa
import matplotlib.pyplot as plt

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
DATABASE = f'{MYROOT}/{DATABASE}'


def fetch_last_day(hours_to_fetch):
    """
    ...
    """
    global DATABASE
    config = glib.add_time_line({'grouping': '%m-%d %Hh',
                                 'period': hours_to_fetch,
                                 'timeframe': 'hour',
                                 'database': DATABASE,
                                 'table': 'ups'
                                 })
    volt_in, data_lbls = glib.get_historic_data(config, parameter='volt_in')
    volt_bat, data_lbls = glib.get_historic_data(config, parameter='volt_bat')
    charge_bat, data_lbls = glib.get_historic_data(config, parameter='charge_bat')
    load_ups, data_lbls = glib.get_historic_data(config, parameter='load_ups')
    runtime_bat, data_lbls = glib.get_historic_data(config, parameter='runtime_bat')
    return data_lbls, volt_in, charge_bat, load_ups, runtime_bat, volt_bat


def fetch_last_month(days_to_fetch):
    """
    ...
    """
    global DATABASE
    config = glib.add_time_line({'grouping': '%m-%d',
                                 'period': days_to_fetch,
                                 'timeframe': 'day',
                                 'database': DATABASE,
                                 'table': 'ups'
                                 })
    volt_in, data_lbls = glib.get_historic_data(config, parameter='volt_in')
    volt_bat, data_lbls = glib.get_historic_data(config, parameter='volt_bat')
    charge_bat, data_lbls = glib.get_historic_data(config, parameter='charge_bat')
    load_ups, data_lbls = glib.get_historic_data(config, parameter='load_ups')
    runtime_bat, data_lbls = glib.get_historic_data(config, parameter='runtime_bat')
    return data_lbls, volt_in, charge_bat, load_ups, runtime_bat, volt_bat


def plot_graph(output_file, data_tuple, plot_title):
    """
    Create graphs
    """
    data_lbls = data_tuple[0]
    volt_in = data_tuple[1][:, 0]
    volt_in_min = data_tuple[1][:, 1]
    volt_in_max = data_tuple[1][:, 2]
    charge_bat = data_tuple[2][:, 0]
    charge_bat_min = data_tuple[2][:, 1]
    charge_bat_max = data_tuple[2][:, 2]
    load_ups = data_tuple[3][:, 0]
    load_ups_min = data_tuple[3][:, 1]
    load_ups_max = data_tuple[3][:, 2]
    runtime_bat = data_tuple[4][:, 0]
    runtime_bat_min = data_tuple[4][:, 1]
    runtime_bat_max = data_tuple[4][:, 2]
    volt_bat = data_tuple[5][:, 0]
    volt_bat_min = data_tuple[5][:, 1]
    volt_bat_max = data_tuple[5][:, 2]


    """
    --- Start debugging:
    np.set_printoptions(precision=3)
    print("data_lbls   : ", np.size(data_lbls), data_lbls[-5:])
    print(" ")
    print("temperatuur : ", np.size(volt_in), volt_in[-5:])
    print("vochtigheid : ", np.size(load_ups), load_ups[-5:])
    print("vochtgehalte: ", np.size(moist), moist[-5:])
    print(" ")
    print("luchtdruk   : ", np.size(charge_bat), charge_bat[-5:])
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

    # *** VOLTAGE / LOAD
    plt.rc('font', size=fig_fontsize)
    dummy, ax1 = plt.subplots(1, figsize=(fig_x, fig_y))

    """
    # ###############################
    # Create a line plot of volt_in/load_ups
    # ###############################
    """

    # LOAD
    ahpla = 0.4
    ax1.errorbar(tick_pos, load_ups,
                 yerr=[load_ups - load_ups_min, load_ups_max - load_ups],
                 elinewidth=10,
                 label='Load',
                 alpha=ahpla,
                 color='blue',
                 marker='o'
                 )
    ax1.set_ylabel("[%]")
    ax1.legend(loc='upper left', framealpha=0.2)
    # y_lo = int(min(load_ups) / 5) * 5
    # y_hi = int(max(load_ups) / 5) * 5 + 5
    # ax1.set_ylim([y_lo, y_hi])

    # Set general plotting stuff
    ax1.set_xlabel("Datetime")
    ax1.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    plt.xticks(tick_pos, data_lbls, rotation=-60)

    ax2 = ax1.twinx()

    # volt_in
    ahpla = 0.7
    ax2.errorbar(tick_pos, volt_in,
                 yerr=[volt_in - volt_in_min, volt_in_max - volt_in],
                 elinewidth=5,
                 label='Line In',
                 alpha=ahpla,
                 color='red',
                 marker='o'
                 )
    ax2.plot(tick_pos, volt_bat,
             label='Battery',
             alpha=ahpla,
             color='black',
             marker='.'
             )
    ax2.set_ylabel("[V]")
    ax2.legend(loc='upper right', framealpha=0.2)
    # y_lo = min(int(min(volt_in)) - 1, int(min(volt_bat)) - 1)
    # y_hi = max(int(max(volt_in)) + 1, int(max(volt_bat)) + 1)
    # if y_lo > 19:
    #     y_lo = 19
    # if y_hi < 22:
    #     y_hi = 22
    # ax2.set_ylim([y_lo, y_hi])

    # Fit every nicely
    plt.title(f'{plot_title}')
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}V.png', format='png')

    # *** BATTERY CHARGE
    plt.rc('font', size=fig_fontsize)
    dummy, ax3 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of charge_bat
    # ###############################
    """
    ax3.bar(tick_pos, charge_bat_min,
            width=bar_width,
            label='Charge (min)',
            alpha=ahpla,
            color='lightgreen',
            align='center',
            bottom=0
            )
    ax3.bar(tick_pos, charge_bat_max - charge_bat_min,
            width=bar_width,
            label='Charge (max)',
            alpha=ahpla,
            color='green',
            align='center',
            bottom=charge_bat_min
            )

    # Set Axes stuff
    ax3.set_ylabel("[%]")
    ax3.set_xlabel("Datetime")
    ax3.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax3.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    # y_lo = min(charge_bat_min) - 2
    # y_hi = max(charge_bat_max) + 2
    # if y_lo > 990:
    #     y_lo = 990
    # if y_hi < 1020:
    #     y_hi = 1020
    # ax3.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}CHG.png', format='png')

    # *** TOTAL VOC
    plt.rc('font', size=fig_fontsize)
    dummy, ax4 = plt.subplots(1, figsize=(fig_x, fig_y))
    """
    # ###############################
    # Create a bar plot of total VOCs
    # ###############################
    """
    ax4.bar(tick_pos, runtime_bat_min,
            width=bar_width,
            label='runtime (min)',
            alpha=ahpla,
            color='magenta',
            align='center',
            bottom=0
            )
    ax4.bar(tick_pos, runtime_bat_max - runtime_bat_min,
            width=bar_width,
            label='runtime (max)',
            alpha=ahpla,
            color='purple',
            align='center',
            bottom=runtime_bat_min
            )

    # Set Axes stuff
    ax4.set_ylabel("runtime [min]")
    ax4.set_xlabel("Datetime")
    ax4.grid(which='major', axis='y', color='k', linestyle='--', linewidth=0.5)
    ax4.legend(loc='upper left', framealpha=0.2)

    # Set plot stuff
    plt.xticks(tick_pos, data_lbls, rotation=-60)
    # plt.title(f'{plot_title}')

    # Fit every nicely
    plt.xlim([min(tick_pos) - bar_width, max(tick_pos) + bar_width])
    # y_lo = min(runtime_bat) - 10
    # y_hi = max(runtime_bat) + 10
    # if y_lo > 0:
    #     y_lo = 0
    # if y_hi < 1000:
    #     y_hi = int(y_hi / 100) * 100 + 100
    # ax4.set_ylim([y_lo, y_hi])
    plt.tight_layout()
    plt.savefig(fname=f'{output_file}RUN.png', format='png')


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
    parser.add_argument('-hr', '--hours', type=int, help='create an hour-trend of <HOURS>')
    parser.add_argument('-d', '--days', type=int, help='create a day-trend of <DAYS>')
    OPTION = parser.parse_args()
    if OPTION.hours == 0:
        OPTION.hours = 50
    if OPTION.days == 0:
        OPTION.days = 50
    main()
