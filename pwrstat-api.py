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

class pwrstat_rest(Resource):
    def get(self):
        return jsonify(get_status())


class pwrstat_mqtt:
    
    def __init__(self, *args, **kwargs):
      


class pwrstat:
  
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

        mqtt_schema = vol.Schema(
            {
                vol.Required("topic"): str,
                vol.Required("refresh"): int,
                vol.Required("qos"): int,
                vol.Required("retained"): bool,
            }
        )

        rest_schema = vol.Schema(
            {
                vol.Required("port"): vol.All(int, vol.Range(min=1025, max=65535)),
                vol.Required("bind_address"): vol.All(
                    str, vol.Length(min=7, max=15), vol.Match(VALID_IP_REGEX)
                ),
            }
        )

        if self.mqttconfig is not None:
            print(self.mqttconfig)
            mqtt_schema(self.mqttconfig)
            schedule.every(self.mqttconfig.get("refresh")).seconds.do(get_status)

        if self.restconfig is not None:
            rest_schema(self.restconfig)
            api.add_resource(pwrstat_rest, "/pwrstat")  # return all parameters
            app.run(
                port=self.restconfig.get("port"),
                host=self.restconfig.get("bind_address"),
            )

def get_status():
    status = (
        subprocess.Popen(["pwrstat", "-status"], stdout=subprocess.PIPE)
        .communicate()[0]
        .decode("utf-8")
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

if __name__ == "__main__":
    pwrstat()
