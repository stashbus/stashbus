FROM python:3.12-bookworm as builder

FROM builder as stashbus_mqtt_publisher
RUN --mount=type=bind,source=.,target=/src/stashbus pip install  --no-cache-dir -e /src/stashbus/db_models /src/stashbus/mqtt_publishers
ENTRYPOINT [ "stashbus" ]

FROM builder as stashbus_mqtt_stasher
RUN --mount=type=bind,source=.,target=/src/stashbus pip install  --no-cache-dir -e /src/stashbus/mqtt_stasher
ENTRYPOINT [ "stashbus-mqtt-stasher" ]

FROM builder as stashbus_web
RUN --mount=type=bind,source=.,target=/src/stashbus,relabel=shared pip install  --no-cache-dir -e /src/stashbus/db_models /src/stashbus/web
WORKDIR /src/stashbus/web
ENTRYPOINT [ "python", "manage.py", "runserver" ]
CMD [ "0.0.0.0:8000" ]
