FROM python:3.8-slim
LABEL Description="CyberPower PowerPanel"
LABEL Maintainer="Daniel Winks"

COPY *.py requirements.txt PPL-1.3.3-64bit.deb init.sh pwrstat.yaml /

RUN apt-get update && apt-get dist-upgrade -y && \
    apt-get install -y procps && \
    chmod +x /init.sh && chmod +x /pwrstat_api.py && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    apt-get install -y /PPL-1.3.3-64bit.deb && \
    apt-get -y --purge autoremove && apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/* /PPL-1.3.3-64bit.deb

CMD ["/init.sh"]
