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
        pass
        # if flask.request.form.get('Control') == 'Instellingen...':
        #     print("Requesting access to Controller")
        #     return flask.redirect(flask.url_for('controller'))

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
    gld = KRAT.get_latest_data('volt_bat, load_ups, charge_bat')
    return flask.render_template('state.html',
                                 room=f'{KRAT.ROOM_ID}',
                                 volt_in=f"{gld[0]:.1f} \u00B0C",
                                 volt_in_img=th_img,
                                 load_ups=f"{gld[1]:.1f} %",
                                 moisture=f"{mst:.1f} g/m\u00B3",
                                 moisture_img=m_img,
                                 charge_bat=f"{gld[2]:.0f} mbara",
                                 charge_bat_img=p_img,
                                 voc=f"{gld[3]:.0f} ppb",
                                 voc_img=v_img,
                                 co2=f"{gld[4]:.0f} ppm",
                                 co2_img=c_img,
                                 freq_img=f_img
                                 )
