import os
from asyncio import sleep
from stashbus.http_common import StashRESTClient
from stashbus.models.mqtt_models import Quote, Price
from pymodbus.framer.base import FramerType
from pymodbus.client.tcp import AsyncModbusTcpClient
from pymodbus import ModbusException
import asyncio
import motor
from motor.motor_asyncio import (
    AsyncIOMotorDatabase as Database,
    AsyncIOMotorCollection as Collection,
)
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

src = StashRESTClient(3, "http://web:8000")


async def run_async_simple_client(host: str, port: int):
    """Run async client."""
    logging.info(f"Will connect to modbus server: {host} {port}")

    client = AsyncModbusTcpClient(
        host,
        port=port,
        framer=FramerType.SOCKET,
    )
    logging.info("Connecting to DB")
    mongodb_creds = await src.aiosecret("mongodb_creds")
    mongo = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb://{mongodb_creds}@mongo:27017/"
    )
    stashbus_db: Database = mongo["stashbus"]
    crypto_data: Collection = stashbus_db["modbus_crypto"]

    logging.info("connecting to server")
    await client.connect()

    while True:
        try:
            # See all calls in client_calls.py
            rr = await client.read_holding_registers(10, count=2, slave=0)
        except ModbusException as exc:
            logging.error(f"Received ModbusException({exc}) from library")
            client.close()
            return
        if rr.isError():
            logging.error(f"Received exception from device ({rr})")
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            client.close()
            return
        logging.info(rr.registers)
        value_int32 = client.convert_from_registers(
            rr.registers, data_type=client.DATATYPE.INT32
        )
        quote = Quote(received_at=datetime.now(), price=Price(USD=value_int32))
        await crypto_data.insert_one(quote.model_dump())
        logging.info(f"Saved int32: {value_int32}")
        await sleep(10)


def main():
    asyncio.run(
        run_async_simple_client(os.environ["MODBUS_HOST"], os.environ["MODBUS_PORT"])
    )
