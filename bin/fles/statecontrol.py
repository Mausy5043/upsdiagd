#!/usr/bin/env python3

import base64

# noinspection PyUnresolvedReferences
import flask
import numpy as np
# noinspection PyUnresolvedReferences
from fles import app
# noinspection PyUnresolvedReferences
from fles import kratlib

KRAT = kratlib.Fles()


@app.route("/", methods=['GET', 'POST'])
@app.route("/state", methods=['GET', 'POST'])
def state():
    global KRAT
    if flask.request.method == 'POST':
        if flask.request.form.get('Control') == 'Instellingen...':
            print("Requesting access to Controller")
            return flask.redirect(flask.url_for('controller'))

    if flask.request.method == 'GET':
        pass

    th_img = "".join(["data:image/png;base64,",
                      str(base64.b64encode(open("/tmp/aircon/site/img/pastday_TH.png",
                                                "rb").read()))[2:-1]]
                     )
    m_img = "".join(["data:image/png;base64,",
                     str(base64.b64encode(open("/tmp/aircon/site/img/pastday_M.png",
                                               "rb").read()))[2:-1]]
                    )
    p_img = "".join(["data:image/png;base64,",
                     str(base64.b64encode(open("/tmp/aircon/site/img/pastday_P.png",
                                               "rb").read()))[2:-1]]
                    )
    v_img = "".join(["data:image/png;base64,",
                     str(base64.b64encode(open("/tmp/aircon/site/img/pastday_VOC.png",
                                               "rb").read()))[2:-1]]
                    )
    c_img = "".join(["data:image/png;base64,",
                     str(base64.b64encode(open("/tmp/aircon/site/img/pastday_CO2.png",
                                               "rb").read()))[2:-1]]
                    )
    f_img = "".join(["data:image/png;base64,",
                     str(base64.b64encode(open("/tmp/aircon/site/img/pastday_F.png",
                                               "rb").read()))[2:-1]]
                    )
    gld = KRAT.get_latest_data('temperature_ac, humidity, pressure, voc, co2')
    mst = moisture(gld[0], gld[1], gld[2])
    return flask.render_template('state.html',
                                 room=f'{KRAT.ROOM_ID}',
                                 temperature=f"{gld[0]:.1f} \u00B0C",
                                 temperature_img=th_img,
                                 humidity=f"{gld[1]:.1f} %",
                                 moisture=f"{mst:.1f} g/m\u00B3",
                                 moisture_img=m_img,
                                 pressure=f"{gld[2]:.0f} mbara",
                                 pressure_img=p_img,
                                 voc=f"{gld[3]:.0f} ppb",
                                 voc_img=v_img,
                                 co2=f"{gld[4]:.0f} ppm",
                                 co2_img=c_img,
                                 freq_img=f_img
                                 )


@app.route("/controller", methods=['GET', 'POST'])
def controller():
    global KRAT
    message = "o.O"
    current_state = KRAT.get_ctrl_state()
    temperature_ctrl = 0
    humidity_ctrl = 0
    fan_ctrl = 0
    if flask.request.method == 'POST':
        if flask.request.form.get('Status') == 'Status':
            return flask.redirect(flask.url_for('state'))
        if flask.request.form.get('Manual') == 'MANUAL':
            KRAT.set('OPERATOR', -1)  # human in control of airco via local panel
            KRAT.set('Mode_SP', 0)
        if flask.request.form.get('SemAut') == 'SEMI-AUTO':
            KRAT.set('OPERATOR', 0)  # human in control of airco via application
        if flask.request.form.get('Automaat') == 'AUTO':
            KRAT.set('OPERATOR', 1)  # application in control human sets SP
            KRAT.set('Mode_SP', 0)
        if flask.request.form.get('Remote') == 'REMOTE':
            KRAT.set('OPERATOR', 2)  # application in control of airco; pre-defined SP
            KRAT.set('Mode_SP', 0)
        if flask.request.form.get('Tctrl') == '+':
            KRAT.set('Temperature_SP', KRAT.get('Temperature_SP') + KRAT.get('Temperature_dSP'))
        if flask.request.form.get('Tctrl') == '-':
            KRAT.set('Temperature_SP', KRAT.get('Temperature_SP') - KRAT.get('Temperature_dSP'))
        if flask.request.form.get('Hctrl') == '+':
            KRAT.set('Humidity_SP', KRAT.get('Humidity_SP') + KRAT.get('Humidity_dSP'))
        if flask.request.form.get('Hctrl') == '-':
            KRAT.set('Humidity_SP', KRAT.get('Humidity_SP') - KRAT.get('Humidity_dSP'))
        if flask.request.form.get('Fctrl') == '+':
            KRAT.set('Fan_SP', KRAT.get('Fan_SP') + KRAT.get('Fan_dSP'))
        if flask.request.form.get('Fctrl') == '-':
            KRAT.set('Fan_SP', KRAT.get('Fan_SP') - KRAT.get('Fan_dSP'))
        if flask.request.form.get('ModCtrl') == 'OFF':
            KRAT.set('Mode_SP', -1)  # OFF
        if flask.request.form.get('ModCtrl') == 'AUTO':
            KRAT.set('Mode_SP', 0)  # AUTO
        if flask.request.form.get('ModCtrl') == 'COOL':
            KRAT.set('Mode_SP', 1)  # COOL
        if flask.request.form.get('ModCtrl') == 'DRY':
            KRAT.set('Mode_SP', 2)  # DRY
        if flask.request.form.get('ModCtrl') == 'HEAT':
            KRAT.set('Mode_SP', 3)  # HEAT
        if flask.request.form.get('ModCtrl') == 'FAN ONLY':
            KRAT.set('Mode_SP', 4)  # FAN ONLY

    if flask.request.method == 'GET':
        pass

    # Display the current SP. If no numeric value is provided, show the current temperature.
    try:
        temperature_sp = float(KRAT.get_ctrl('stemp'))
    except ValueError:
        temperature_sp = float(KRAT.get_ctrl('htemp'))
    humidity_sp = KRAT.get('Humidity_SP')
    fan_sp = KRAT.get_ctrl('f_rate')
    mode_sp = KRAT.get('Mode_SP')
    operator_sp = KRAT.get('OPERATOR')

    temperature_ctrl = humidity_ctrl = fan_ctrl = 0
    if operator_sp == -1:
        # MANUAL
        message = "Airco staat op handbediening."
    if operator_sp == 0:
        # SEMI-AUTO
        message = "Airco wordt door u bediend via de computer."
        if mode_sp == -1:
            pass
        if mode_sp == 0:
            pass
        if mode_sp == 1:
            temperature_ctrl = 1
            fan_ctrl = 1
        if mode_sp == 2:
            humidity_ctrl = 1
            fan_ctrl = 1
        if mode_sp == 3:
            temperature_ctrl = 1
            fan_ctrl = 1
        if mode_sp == 4:
            fan_ctrl = 1
    if operator_sp == 1:
        # AUTO
        message = "Airco wordt door de computer bediend op basis van uw instellingen."
        temperature_ctrl = 1
        humidity_ctrl = 1
    if operator_sp == 2:
        # REMOTE
        message = "Airco wordt door de computer bediend."

    message = f"{current_state}"
    gld = KRAT.get_latest_data('temperature_ac, humidity, pressure, voc, co2')
    mst = moisture(gld[0], gld[1], gld[2])
    moisture_sp = moisture(temperature_sp, humidity_sp, gld[2])
    return flask.render_template('controller.html',
                                 message=message,
                                 ope=operator_sp,
                                 mode=mode_sp,
                                 tempctrl=temperature_ctrl,
                                 tempset=f"{temperature_sp:.1f} \u00B0C",
                                 humctrl=humidity_ctrl,
                                 humset=f"{humidity_sp:.1f} %",
                                 moistset=f"{moisture_sp:.1f} g/m\u00B3",
                                 fanctrl=fan_ctrl,
                                 fanset=fan_sp,
                                 room=f'{KRAT.ROOM_ID}',
                                 temperature=f"{gld[0]:.1f} \u00B0C",
                                 humidity=f"{gld[1]:.1f} %",
                                 moisture=f"{mst:.1f} g/m\u00B3",
                                 pressure=f"{gld[2]:.0f} mbara",
                                 voc=f"{gld[3]:.0f} ppb",
                                 co2=f"{gld[4]:.0f} ppm"
                                 )


def moisture(temperature, relative_humidity, pressure):
    kelvin = temperature + 273.15
    pascal = pressure * 100
    rho = (287.04 * kelvin) / pascal

    es = 611.2 * np.exp(17.67 * (kelvin - 273.15) / (kelvin - 29.65))
    rvs = 0.622 * es / (pascal - es)
    rv = relative_humidity / 100. * rvs
    qv = rv / (1 + rv)
    moistair = qv * rho * 1000  # g water per m3 air
    return np.array(moistair)
