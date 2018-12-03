FROM python:3-stretch
LABEL Description="Eclipse Mosquitto MQTT Broker"
LABEL Maintainer="Daniel Winks"

COPY pwrstat-api.py requirements.txt powerpanel_*_amd64.deb init.sh /

RUN apt update && apt dist-upgrade -y && rm -rf /var/lib/apt/lists/* && \
    chmod +x /init.sh && chmod +x /pwrstat-api.py && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    dpkg -i powerpanel_*_amd64.deb

HEALTHCHECK --interval=30s --timeout=3s --start-period=45s --retries=5 \
    CMD curl -sI http://192.168.1.20:5002/pwrstat || exit 1

ENTRYPOINT "/init.sh"