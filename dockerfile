FROM python:3-stretch
MAINTAINER Daniel Winks

VOLUME /src
COPY pwrstat-api.py requirements.txt powerpanel_*_amd64.deb init.sh /src/
WORKDIR /src
RUN chmod +x /src/init.sh
RUN chmod +x /src/pwrstat-api.py
RUN pip install --trusted-host pypi.python.org -r requirements.txt && \
    dpkg -i powerpanel_*_amd64.deb

ENTRYPOINT "/src/init.sh"