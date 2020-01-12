"""Get output from pwrstat program and send results to REST or MQTT clients."""
from flask import Flask, Response, make_response, jsonify

import pwrstat_api
import pwrstat_mqtt

APP = Flask(__name__)


@APP.route("/pwrstat", methods=["GET"])
def pwrstat() -> Response:
    """Responder for get requests."""
    status = pwrstat_api.get_status()
    if status is not None:
        return jsonify(status)
    data = {"message": "Unavailable: pwrstatd failure", "code": "ERROR"}
    return make_response(jsonify(data), 503)


@APP.route("/health", methods=["GET"])
def health() -> Response:
    """Responder for get requests."""
    data = {"message": "OK", "code": "SUCCESS"}
    return make_response(jsonify(data), 200)


@APP.route("/mqtthealth", methods=["GET"])
def mqtthealth() -> Response:
    """Responder for get requests."""
    mqtt_status = pwrstat_mqtt.is_connected()
    if mqtt_status:
        data = {"message": "OK", "code": "SUCCESS"}
        return make_response(jsonify(data), 200)
    data = {"message": "MQTT Disconnected!", "code": "ERROR"}
    return make_response(jsonify(data), 503)


if __name__ == "__main__":
    pass
