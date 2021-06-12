#!/usr/bin/env python3

import base64

import flask
from fles import app  # noqa
from fles import kratlib  # noqa

KRAT = kratlib.Fles()


@app.route("/", methods=['GET', 'POST'])
@app.route("/state", methods=['GET', 'POST'])
def state():
    global KRAT
    if flask.request.method == 'POST':
        pass

    if flask.request.method == 'GET':
        pass

    chg_img = "".join([
        "data:image/png;base64,",
        str(
            base64.b64encode(
                open("/tmp/upsdiagd/site/img/pastday_CHG.png",
                     "rb").read()))[2:-1]
    ])
    run_img = "".join([
        "data:image/png;base64,",
        str(
            base64.b64encode(
                open("/tmp/upsdiagd/site/img/pastday_RUN.png",
                     "rb").read()))[2:-1]
    ])
    v_img = "".join([
        "data:image/png;base64,",
        str(
            base64.b64encode(
                open("/tmp/upsdiagd/site/img/pastday_V.png",
                     "rb").read()))[2:-1]
    ])
    # gld = KRAT.get_latest_data('volt_bat, load_ups, charge_bat')
    return flask.render_template(
        'state.html',
        volt_in="n/a",  # f"{gld[0]:.1f} \u00B0C",
        volt_in_img=v_img,
        load_ups="n/a",  # f"{gld[1]:.1f} %",
        charge_bat="n/a",  # f"{gld[2]:.0f} mbara",
        charge_bat_img=chg_img,
        run="n/a",  # f"{gld[3]:.0f} ppb",
        run_img=run_img)
