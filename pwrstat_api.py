#!/usr/local/bin/python3
"""Get output from pwrstat program and send results to REST or MQTT clients."""
from threading import Thread
import logging
from subprocess import DEVNULL, Popen, PIPE
from typing import Any, Dict, List, Optional

from ruamel.yaml import YAML as yaml
from ruamel.yaml import YAMLError

import pwrstat_prometheus
import pwrstat_mqtt
import pwrstat_rest
from pwrstat_schemas import PWRSTAT_API_SCHEMA, MQTT_SCHEMA, REST_SCHEMA, PROMETHEUS_SCHEMA

_LOGGER = logging.getLogger("PwrstatApi")
YAML = yaml(typ="safe")


class PwrstatApi:
    """Get output from pwrstat program and send results to REST or MQTT clients."""

    def __init__(self) -> None:
        """Initialize Pwrstat class."""
        _start_pwrstatd_watchdog()
        _process_config()


def _process_config() -> None:
    """Process YAML config file. Starts servers if configured."""
    with open("pwrstat.yaml") as file:
        try:
            yaml_config: Dict[str, Any] = YAML.load(file)
        except YAMLError as ex:
            _LOGGER.log(level=logging.ERROR, msg=ex)

    pwrstat_api_yaml: Dict[str, Any] = yaml_config.get("pwrstat_api") or {}
    pwrstat_api_config: Dict[str, Any] = PWRSTAT_API_SCHEMA(pwrstat_api_yaml)

    _LOGGER.setLevel(pwrstat_api_config["log_level"])

    if "mqtt" in yaml_config:
        _start_mqtt(yaml_config["mqtt"])

    if "prometheus" in yaml_config:
        _start_prometheus(yaml_config["prometheus"])

    if "rest" in yaml_config:
        _start_rest(yaml_config["rest"])


def get_status() -> Optional[Dict[str, str]]:
    """Return status from pwrstat program."""
    _LOGGER.info("Getting status from pwrstatd...")
    status: str = Popen(
        ["pwrstat", "-status"], stdout=PIPE, stderr=DEVNULL
    ).communicate()[0].decode("utf-8")
    status_dict = _get_status_dict(status)
    if len(status_dict) > 1:
        return status_dict
    _LOGGER.warning("Pwrstatd did not return any data.")
    _LOGGER.warning("Check USB connection and UPS.")
    _LOGGER.warning("If USB device frequently changes, consider creating a udev rule.")
    return None


def _get_status_dict(status: str) -> Dict[str, str]:
    """Return status dict from status message."""
    status_list: List[List[str]] = []
    for line in status.splitlines():
        line = line.lstrip()
        line = line.replace(". ", ";")
        line = line.replace(".", "")
        lines: List[str] = line.split(";")
        if len(lines) > 1:
            status_list.append(lines)
    return {k[0]: k[1] for k in status_list}


def _start_pwrstatd() -> Popen:
    """Start pwrstatd daemon to allow communication with UPS."""
    return Popen(["/usr/sbin/pwrstatd", "start"], stdout=DEVNULL, stderr=DEVNULL)


def _start_pwrstatd_watchdog() -> None:
    """Start pwrstatd and ensure it's running."""
    pwrstatd_process = _start_pwrstatd()

    # def watchdog():
    #     while True:
    #         time.sleep(30)
    #         if pwrstatd_process.poll() is None:
    #             _start_pwrstatd()

    # Thread(target=watchdog).start()


def _start_mqtt(mqtt_config_yaml: Dict[str, Any]) -> None:
    """Start MQTT client."""
    mqtt_config: Dict[str, Any] = MQTT_SCHEMA(mqtt_config_yaml)
    _LOGGER.info("Initializing MQTT...")
    pwrstatmqtt = pwrstat_mqtt.PwrstatMqtt(mqtt_config=mqtt_config)
    Thread(target=pwrstatmqtt.loop).start()


def _start_prometheus(prometheus_config_yaml: Dict[str, Any]) -> None:
    """Start Prometheus client."""
    _LOGGER.info("Initializing Prometheus...")
    prometheus_config: Dict[str, Any] = PROMETHEUS_SCHEMA(prometheus_config_yaml)

    from prometheus_client.core import CollectorRegistry
    from prometheus_client import make_wsgi_app
    from wsgiref.simple_server import make_server

    registry = CollectorRegistry(auto_describe=True)
    registry.register(pwrstat_prometheus.CustomCollector(prometheus_config["labels"]))

    app = make_wsgi_app(registry)
    httpd = make_server(prometheus_config["bind_address"], prometheus_config["port"], app)
    Thread(target=httpd.serve_forever).start()
    _LOGGER.info("After Prometheus")


def _start_rest(rest_config_yaml: Dict[str, Any]) -> None:
    """Start REST client."""
    _LOGGER.info("Initializing REST...")
    rest_config: Dict[str, Any] = REST_SCHEMA(rest_config_yaml)
    pwrstat_rest.APP.run(port=rest_config["port"], host=rest_config["bind_address"])
    _LOGGER.info("After REST")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    _LOGGER.info("Starting Pwrstat_API...")
    PwrstatApi()
