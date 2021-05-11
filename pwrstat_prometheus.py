"""Get output from pwrstat program and send results to REST or MQTT clients."""
import re
from typing import Dict

from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily

import pwrstat_api


class CustomCollector(object):
    def __init__(self, labels: Dict[str, str] = None):
        if labels is None:
            labels = {}

        self.label_names = list(labels.keys())
        self.label_values = list(labels.values())

    def collect(self):
        status = pwrstat_api.get_status()
        if status is None:
            return

        info = InfoMetricFamily("pwrstat_status_info", "General info about the UPS", labels=self.label_names)
        info.add_metric(labels=self.label_values, value={
            "rating_voltage": status["Rating Voltage"],
            "firmware_number": status["Firmware Number"],
            "rating_power": status["Rating Power"],
            "last_power_event": status["Last Power Event"],
            "line_interaction": status["Line Interaction"],
            "test_result": status["Test Result"],
        })
        yield info

        state = GaugeMetricFamily("pwrstat_status_state", "State value enum", labels=(self.label_names + ["state"]))
        state.add_metric(labels=(self.label_values + ["normal"]), value=(status["State"] == "Normal"))
        yield state

        state = GaugeMetricFamily("pwrstat_status_supply", "Power supplied by", labels=(self.label_names + ["supply"]))
        state.add_metric(
            labels=(self.label_values + ["utility"]),
            value=(status["Power Supply by"] == "Utility Power"),
        )
        state.add_metric(
            labels=(self.label_values + ["battery"]),
            value=(status["Power Supply by"] == "Battery"),
        )
        yield state

        bat_cap = GaugeMetricFamily("pwrstat_status_battery_capacity", "Current battery capacity",
                                    unit="percent", labels=self.label_names)
        bat_cap.add_metric(labels=self.label_values,
                           value=re.search(r"\d+(?:\.\d+)?", status["Battery Capacity"]).group())
        yield bat_cap

        load = GaugeMetricFamily("pwrstat_status_load", "Current load on supply",
                                 unit="watts", labels=self.label_names)
        load.add_metric(labels=self.label_values,
                        value=re.search(r"\d+(?:\.\d+)?", status["Load"]).group())
        yield load

        output_voltage = GaugeMetricFamily("pwrstat_status_output_voltage", "Output voltage to connected devices",
                                           unit="volts", labels=self.label_names)
        output_voltage.add_metric(labels=self.label_values,
                                  value=re.search(r"\d+(?:\.\d+)?", status["Output Voltage"]).group())
        yield output_voltage

        remaining_runtime = GaugeMetricFamily("pwrstat_status_remaining_runtime",
                                              "Estimated remaining battery time",
                                              unit="minutes", labels=self.label_names)
        remaining_runtime.add_metric(labels=self.label_values,
                                     value=re.search(r"\d+(?:\.\d+)?", status["Remaining Runtime"]).group())
        yield remaining_runtime

        utility_voltage = GaugeMetricFamily("pwrstat_status_utility_voltage",
                                            "Input voltage from the wall",
                                            unit="volts", labels=self.label_names)
        utility_voltage.add_metric(labels=self.label_values,
                                   value=re.search(r"\d+(?:\.\d+)?", status["Utility Voltage"]).group())
        yield utility_voltage


if __name__ == "__main__":
    from prometheus_client.core import CollectorRegistry
    from prometheus_client import make_wsgi_app
    from wsgiref.simple_server import make_server

    registry = CollectorRegistry(auto_describe=True)
    registry.register(CustomCollector({
        "test": "test",
    }))

    app = make_wsgi_app(registry)
    httpd = make_server('', 9222, app)
    httpd.serve_forever()
