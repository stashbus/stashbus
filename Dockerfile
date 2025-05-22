FROM python:3.12-bookworm as builder
RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade pip
RUN mkdir -p /src/stashbus
WORKDIR /src/stashbus
COPY modbus modbus/
COPY models models/
COPY mqtt_publishers/ mqtt_publishers/
COPY mqtt_stasher/ mqtt_stasher/
COPY web/ web/
RUN --mount=type=cache,target=/root/.cache/pip pip install -e ./models -e ./mqtt_publishers -e ./mqtt_stasher -e ./modbus -e ./web

FROM builder as stashbus_mqtt_publisher
ENTRYPOINT [ "stashbus" ]

FROM builder as stashbus_mqtt_stasher
ENTRYPOINT [ "stashbus-mqtt-stasher" ]

FROM builder as stashbus_modbus
RUN --mount=type=cache,target=/var/cache/apt apt-get update && apt-get install -yqq netcat-openbsd &&  rm -rf /var/lib/apt/lists/*
ENTRYPOINT [ "stashbus-modbus" ]

FROM builder as stashbus_web
WORKDIR /src/stashbus
ENTRYPOINT [ "python", "web/src/stashbus/manage.py", "runserver" ]
CMD [ "0.0.0.0:8000" ]


FROM alpine:latest as stunnel
RUN apk add --no-cache stunnel
COPY certs/stunnel.pem /etc/stunnel/stunnel.pem
RUN chmod 600 /etc/stunnel/stunnel.pem


FROM stunnel as stunnel-client
COPY modbus/stunnel-client.conf /etc/stunnel/stunnel.conf
CMD ["stunnel", "/etc/stunnel/stunnel.conf"]

FROM stunnel as stunnel-server
COPY modbus/stunnel-server.conf /etc/stunnel/stunnel.conf
CMD ["stunnel", "/etc/stunnel/stunnel.conf"]
