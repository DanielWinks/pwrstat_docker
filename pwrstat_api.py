#!/usr/bin/env python3
"""Get output from pwrstat program and send results to REST or MQTT clients."""
import asyncio
import logging
from subprocess import DEVNULL, Popen, PIPE
from typing import Any, Dict, List, Optional

from ruamel.yaml import YAML as yaml
from ruamel.yaml import YAMLError

from pwrstat_mqtt import PwrstatMqtt
from pwrstat_rest import APP
from pwrstat_schemas import PWRSTAT_API_SCHEMA, MQTT_SCHEMA, REST_SCHEMA

LOGGER = logging.getLogger(__name__)
YAML = yaml(typ="safe")


class PwrstatApi:
    """Get output from pwrstat program and send results to REST or MQTT clients."""

    def __init__(self) -> None:
        """Initilize Pwrstat class."""
        process_config()
        asyncio.run(_pwrstatd_watchdog())


def process_config() -> None:
    """Process YAML config file."""
    with open("pwrstat.yaml") as file:
        try:
            yaml_config = YAML.load(file)
        except YAMLError as ex:
            LOGGER.log(level=logging.ERROR, msg=ex)

    if "mqtt" in yaml_config:
        _start_mqtt(yaml_config["mqtt"])

    if "rest" in yaml_config:
        _start_rest(yaml_config["rest"])

    pwrstat_api_yaml: Dict[str, Any] = yaml_config.get("pwrstat_api") or {}
    pwrstat_api_config: Dict[str, Any] = PWRSTAT_API_SCHEMA(pwrstat_api_yaml)
    log_level = pwrstat_api_config["log_level"]
    LOGGER.setLevel(log_level)


def get_status() -> Optional[Dict[str, str]]:
    """Return status from pwrstat program."""
    LOGGER.log(level=logging.DEBUG, msg="Getting status from pwrstatd...")
    status: str = Popen(
        ["pwrstat", "-status"], stdout=PIPE, stderr=DEVNULL
    ).communicate()[0].decode("utf-8")
    status_list: List[List[str]] = []
    for line in status.splitlines():
        line = line.lstrip()
        line = line.replace(". ", ";")
        line = line.replace(".", "")
        lines: List[str] = line.split(";")
        if len(lines) > 1:
            status_list.append(lines)
    if len(status_list) > 1:
        return {k[0]: k[1] for k in status_list}
    LOGGER.log(level=logging.WARNING, msg="Pwrstatd did not return any data.")
    LOGGER.log(level=logging.WARNING, msg="Check USB connection and UPS.")
    LOGGER.log(
        level=logging.WARNING,
        msg="If USB device frequently changes name, consider creating a udev rule.",
    )
    return None


def _start_pwrstatd() -> Popen:
    """Start pwrstatd daemon to allow communication with UPS."""
    return Popen(["/usr/sbin/pwrstatd", "start"], stdout=DEVNULL, stderr=DEVNULL)


async def _pwrstatd_watchdog() -> None:
    """Start pwrstatd and ensure it's running."""
    pwrstatd_process = _start_pwrstatd()
    while True:
        await asyncio.sleep(30)
        if pwrstatd_process.poll() is None:
            _start_pwrstatd()


def _start_mqtt(mqtt_config_yaml: Dict[str, Any]) -> None:
    """Start MQTT client."""
    mqtt_config: Dict[str, Any] = MQTT_SCHEMA(mqtt_config_yaml)
    LOGGER.log(level=logging.INFO, msg="Initializing MQTT...")
    pwrstatmqtt = PwrstatMqtt(mqtt_config=mqtt_config)
    asyncio.run(pwrstatmqtt.loop())


def _start_rest(rest_config_yaml: Dict[str, Any]) -> None:
    """Start REST client."""
    LOGGER.log(level=logging.INFO, msg="Initializing REST...")
    rest_config: Dict[str, Any] = REST_SCHEMA(rest_config_yaml)
    port = rest_config["port"]
    host = rest_config["bind_address"]
    LOGGER.log(
        level=logging.INFO,
        msg=f"Starting REST endpoint, listening on {host}:{port}...",
    )
    APP.run(port=port, host=host)


if __name__ == "__main__":
    LOGGER.setLevel("DEBUG")
    LOGGER.log(level=logging.INFO, msg="Starting Pwrstat_API...")
    PwrstatApi()
