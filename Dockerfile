FROM python:3-slim
LABEL Description="CyberPower PowerPanel"
LABEL Maintainer="Daniel Winks"

COPY pwrstat_api.py requirements.txt powerpanel_*_amd64.deb init.sh pwrstat.yaml /

RUN apt-get update && apt-get dist-upgrade -y && \
    chmod +x /init.sh && chmod +x /pwrstat_api.py && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    dpkg -i powerpanel_*_amd64.deb && \
    apt-get -y --purge autoremove && apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*

HEALTHCHECK --interval=30s --timeout=3s --start-period=45s --retries=5 \
    CMD curl -sI http://127.0.0.1:5002/pwrstat || exit 1

ENTRYPOINT "/init.sh"
