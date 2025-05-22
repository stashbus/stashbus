import asyncio
import logging
from stashbus.http_common import CryptoCompareClient, StashRESTClient, Mempool
from stashbus.db_models import Currency

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
)


logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)


from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore.store import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.client.base import ModbusBaseClient

import logging


# Enable debug logging
logging.basicConfig()
log = logging.getLogger()


async def server():
    # Create a data block for holding registers (type 3x)
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(
            0, [0] * 100
        )  # 100 holding registers, all initialized to 0
    )

    context = ModbusServerContext(slaves=store, single=True)

    # Optional: Set server identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = "Easycon"
    identity.ProductCode = "MC"
    identity.VendorUrl = "https://easycon.cz"
    identity.ProductName = "Modbus test"
    identity.ModelName = "Modbus Model"
    identity.MajorMinorRevision = "1.0"

    mempool = Mempool()
    server = StartAsyncTcpServer(context, identity=identity, address=("0.0.0.0", 502))
    ut = asyncio.create_task(updating_task(context, mempool))
    await asyncio.gather(ut, server)


async def updating_task(context: ModbusServerContext, mempool: Mempool):
    """Update values in server.

    This task runs continuously beside the server
    It will increment some values each two seconds.

    It should be noted that getValues and setValues are not safe
    against concurrent use.
    """
    fc_as_hex = 3
    device_id = 0x00
    address = 10

    # incrementing loop
    while True:
        try:
            message = await mempool.aget_data()
        except Exception as e:
            _logger.warning(f"Failed to fetch or update mempool data: {e}")
        else:
            values = ModbusBaseClient.convert_to_registers(
                int(message.price.USD), ModbusBaseClient.DATATYPE.INT32
            )
            context[device_id].setValues(fc_as_hex, address, values)
            txt = f"updating_task set vals: {values!s} at address {address!s}"
            _logger.debug(txt)
        await asyncio.sleep(30)


def main():
    asyncio.run(server())
