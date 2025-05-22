FROM python:3.12-bookworm as builder


FROM builder as stashbus_mqtt_publisher
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=bind,source=.,target=/src/stashbus pip install -e /src/stashbus/db_models /src/stashbus/mqtt_publishers
ENTRYPOINT [ "stashbus" ]


FROM builder as stashbus_mqtt_stasher
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=bind,source=.,target=/src/stashbus pip install -e /src/stashbus/mqtt_stasher
ENTRYPOINT [ "stashbus-mqtt-stasher" ]


FROM builder as stashbus_modbus
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=bind,source=.,target=/src/stashbus pip install -e /src/stashbus/modbus /src/stashbus/db_models
RUN --mount=type=cache,target=/var/cache/apt apt-get update && apt-get install -yqq netcat-openbsd &&  rm -rf /var/lib/apt/lists/*
ENTRYPOINT [ "stashbus-modbus" ]


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


FROM builder as stashbus_web
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=bind,source=.,target=/src/stashbus,relabel=shared pip install -e /src/stashbus/db_models /src/stashbus/web
WORKDIR /src/stashbus/web
ENTRYPOINT [ "python", "manage.py", "runserver" ]
CMD [ "0.0.0.0:8000" ]
