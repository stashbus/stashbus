import os
import subprocess
import docker.models
import pytest
import docker
import docker.models.containers
import httpx
from stashbus import openweathermap_mqtt_publisher
from unittest.mock import Mock, patch
import py
from time import sleep
from datetime import datetime, timedelta
from typing import Any

CONTENT = b'{"lat":0,"lon":0,"current":{"temp":23.0,"pressure":1023,"humidity":50,"wind_speed":3,"wind_deg":15}}'
MQTT_IMAGE = "eclipse-mosquitto"


@pytest.fixture()
def ca_private_key(tmpdir: py.path.local):
    out = tmpdir / "ca.key"
    subprocess.run(f"openssl genrsa -out {out} 4096", check=True, shell=True)
    return out


@pytest.fixture()
def self_signed_ca_cert(tmpdir: py.path.local, ca_private_key: py.path.local):
    out = tmpdir / "ca.crt"
    config = tmpdir / "extfile.cnf"
    config.write(
        """[ req ]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[ req_distinguished_name ]
C = IN
ST = Karnataka
L = Bengaluru
O = GoLinuxCloud
OU = Sme Organizational Unit
CN = RootCA

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical,CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
"""
    )
    subprocess.run(
        f"openssl req -new -x509 -days 3650 -key {ca_private_key} -out {out} -config {config}",
        check=True,
        shell=True,
    )
    return out


@pytest.fixture()
def server_private_key(tmpdir: py.path.local):
    out = tmpdir / "server.key"
    subprocess.run(f"openssl genrsa -out {out} 4096", check=True, shell=True)
    os.chmod(out, 0o666)
    return out


@pytest.fixture()
def server_cert(
    tmpdir: py.path.local,
    self_signed_ca_cert: py.path.local,
    ca_private_key: py.path.local,
    server_private_key: py.path.local,
):
    csr = tmpdir / "server.csr"
    server_cert = tmpdir / "server.cert.pem"
    config_req = tmpdir / "req.cnf"
    config_req.write(
        """
[req]
distinguished_name = req_distinguished_name
req_extensions = req_ext
prompt = no

[req_distinguished_name]
C   = CZ
ST  = .
L   = Brno
O   = Easycon
OU  = R&D
CN  = mqtt-broker

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = mqtt-broker
DNS.2 = localhost
"""
    )
    subprocess.run(
        f"openssl req -new -key {server_private_key} -out {csr} -config {config_req}",
        check=True,
        shell=True,
    )
    subprocess.run(
        f"openssl x509 -req -in {csr} -CA {self_signed_ca_cert} -CAkey {ca_private_key} -out {server_cert} -CAcreateserial -days 1 -sha256 -extfile {config_req} -extensions req_ext",
        check=True,
        shell=True,
        capture_output=True,
    )
    return server_cert


@pytest.fixture()
def mqtt_broker_container(
    tmpdir: py.path.local,
    self_signed_ca_cert: py.path.local,
    server_cert: py.path.local,
    server_private_key: py.path.local,
):
    mqtt_config_path = tmpdir / "mosquitto.conf"
    mqtt_config_path.write(
        f"""\
listener 1883
cafile /mosquitto/config/ca.crt
certfile /mosquitto/config/server.crt
keyfile /mosquitto/config/server.pem
persistence false
allow_anonymous true
"""
    )
    client = docker.from_env()
    volumes = {
        str(mqtt_config_path): {
            "bind": "/mosquitto/config/mosquitto.conf",
            "mode": "ro,z",
        },
        str(self_signed_ca_cert): {"bind": "/mosquitto/config/ca.crt", "mode": "ro,z"},
        str(server_cert): {"bind": "/mosquitto/config/server.crt", "mode": "ro,z"},
        str(server_private_key): {
            "bind": "/mosquitto/config/server.pem",
            "mode": "ro,z",
        },
    }
    container = client.containers.run(
        MQTT_IMAGE, detach=True, ports={"1883/tcp": 1883}, volumes=volumes
    )
    yield container
    container.remove(force=True)


mock_response = httpx.Response(
    status_code=200,
    content=CONTENT,
    headers={"Content-Type": "application/json"},
    request=httpx.Request("mock", "mock"),
)


def test_calls_http(
    mqtt_broker_container: docker.models.containers.Container,
    self_signed_ca_cert: py.path.local,
):
    #    with patch.object(openweathermap_mqtt_publisher, 'OWM_BASEURL', new="localhost"):
    owm_publisher = openweathermap_mqtt_publisher.OWMPublisher(
        "localhost",
        1883,
        str(self_signed_ca_cert),
        None,
        None,
        "/testing/topic",
        5,
        0,
        0,
        "TEST_APP_KEY",
    )
    with patch.object(
        owm_publisher.http_cli, "get", return_value=mock_response
    ) as httpx_get:
        owm_publisher.mqtt_cli.loop_read()
        owm_publisher.do_work.set()
        owm_publisher.cycle()
        httpx_get.assert_called()


class CallbackExpector(Mock):
    def __init__(self, spec: Any | None = None, side_effect: Any | None = None, return_value: Any = ..., wraps: Any | None = None, name: Any | None = None, spec_set: Any | None = None, parent: Any | None = None, _spec_state: Any | None = None, _new_name: Any = "", _new_parent: Any | None = None, **kwargs: Any) -> None:  # type: ignore
        super().__init__(
            spec,
            side_effect,
            return_value,
            wraps,
            name,
            spec_set,
            parent,
            _spec_state,
            _new_name,
            _new_parent,
            **kwargs,
        )
        self.reset_waiter()

    def reset_waiter(self):
        self.start_call_count = self.call_count

    def waiting(self, timeout: float):
        end = datetime.now() + timedelta(seconds=timeout)
        while datetime.now() < end:
            if self.start_call_count < self.call_count:
                return
            else:
                yield
        else:
            pytest.fail()


def test_connects_mqtt(
    mqtt_broker_container: docker.models.containers.Container,
    self_signed_ca_cert: py.path.local,
):

    with (
        patch(
            "stashbus.openweathermap_mqtt_publisher.OWMPublisher.on_connect",
            CallbackExpector(),
        ) as on_connect,
        patch(
            "stashbus.openweathermap_mqtt_publisher.OWMPublisher.on_connect_fail"
        ) as on_connect_fail,
    ):
        owm_publisher = openweathermap_mqtt_publisher.OWMPublisher(
            mqtt_host="localhost",
            mqtt_port=1883,
            ca_certs=str(self_signed_ca_cert),
            certfile=None,
            keyfile=None,
            topic="/testing/topic",
            period=5,
            lat=0,
            lon=0,
            appid="TEST_APP_KEY",
        )

        for _ in on_connect.waiting(10.0):
            repr(owm_publisher.mqtt_cli.loop_write())
            repr(owm_publisher.mqtt_cli.loop_misc())
            repr(owm_publisher.mqtt_cli.loop_read())
            sleep(0.1)

        on_connect.assert_called_once()
        on_connect_fail.assert_not_called()
