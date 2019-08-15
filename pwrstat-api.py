#!/usr/bin/env python3

import subprocess
import schedule
import time
import voluptuous as vol

from flask import Flask, request
from flask_jsonpify import jsonify
from flask_restful import Api, Resource
from paho.mqtt import publish
from ruamel.yaml import YAML
from typing import Any, Dict, List, Optional

app = Flask(__name__)
api = Api(app)
yaml = YAML(typ="safe")

VALID_IP_REGEX = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"


class pwrstat(Resource):
    def __init__(self, *args, **kwargs):
        with open("pwrstat.yaml") as f:
            try:
                self.yamlconfig = yaml.load(f)
            except yaml.YAMLError as ex:
                print(ex)
            if "mqtt" in self.yamlconfig:
                self.mqttconfig = self.yamlconfig.get("mqtt")
            if "rest" in self.yamlconfig:
                self.restconfig = self.yamlconfig.get("rest")

        mqtt_schema = {
            vol.Schema(
                {
                    vol.Required("topic"): str,
                    vol.Optional("refresh", default=30): int,
                    vol.Optional("qos", default=0): int,
                    vol.Optional("retained", default=true): bool,
                }
            )
        }
        http_schema = {
            vol.Schema(
                {
                    vol.Optional("port", default=5002): All(int, Range(min=1025, max=65535)),
                    vol.Optional("http_bind_address", default="0.0.0.0"): All(
                        str, Length(min=7, max=15), Match(VALID_IP_REGEX)
                    ),
                }
            )
        }
        if self.mqttconfig is not None:
            mqtt_schema(self.yamlconfig)
            schedule.every(self.yamlconfig.get("refresh")).seconds.do(get_status)
        if self.restconfig is not None:
            http_schema(http_schema)
            api.add_resource(pwrstat, "/pwrstat")  # return all parameters

    def get_status(self):
        status = (
            subprocess.Popen(["pwrstat", "-status"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
        )
        statusArr = []
        for line in status.splitlines():
            line = line.lstrip()
            line = line.replace(". ", ";")
            line = line.replace(".", "")
            line = line.split(";")
            if len(line) > 1:
                statusArr.append(line)

        statusDict = {}
        statusDict = {k[0]: k[1] for k in statusArr}
        return statusDict

    def get(self):
        return jsonify(self.get_status())


if __name__ == "__main__":
    app.run(port=5002, host="0.0.0.0")
