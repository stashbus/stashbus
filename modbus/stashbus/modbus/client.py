import os
from asyncio import sleep
from stashbus.http_common import StashRESTClient
from stashbus.db_models import Quote, Price
from pymodbus.framer.base import FramerType
from pymodbus.client.tcp import AsyncModbusTcpClient
from pymodbus import ModbusException
import asyncio
import pymongo
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Dict, Any
from datetime import datetime


src = StashRESTClient(3, "http://web:8000")


async def run_async_simple_client(host: str, port: int):
    """Run async client."""

    client = AsyncModbusTcpClient(
        host,
        port=port,
        framer=FramerType.SOCKET,
    )

    mongodb_creds = src.secret("mongodb_creds")
    mongo = pymongo.MongoClient(f"mongodb://{mongodb_creds}@mongo:27017/")
    stashbus_db: Database = mongo["stashbus"]
    crypto_data: Collection = stashbus_db["modbus_crypto"]

    print("connecting to server")
    await client.connect()

    while True:
        try:
            # See all calls in client_calls.py
            rr = await client.read_holding_registers(10, count=2, slave=0)
        except ModbusException as exc:
            print(f"Received ModbusException({exc}) from library")
            client.close()
            return
        if rr.isError():
            print(f"Received exception from device ({rr})")
            # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
            client.close()
            return
        print(rr.registers)
        value_int32 = client.convert_from_registers(
            rr.registers, data_type=client.DATATYPE.INT32
        )
        quote = Quote(received_at=datetime.now(), price=Price(USD=value_int32))
        crypto_data.insert_one(quote.model_dump())
        print(f"Saved int32: {value_int32}")
        await sleep(10)


def main():
    asyncio.run(
        run_async_simple_client(os.environ["MODBUS_HOST"], os.environ["MODBUS_PORT"])
    )
