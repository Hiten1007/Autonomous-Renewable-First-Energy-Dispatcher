import asyncio
from solar_sensor import solar_sensor
from load_sensor import load_sensor
from carbon_sensor import carbon_sensor
from orchestrator import orchestrator

async def main():
    input_q = asyncio.Queue()
    output_q = asyncio.Queue()

    await asyncio.gather(
        solar_sensor(input_q),
        load_sensor(input_q),
        carbon_sensor(input_q),
        orchestrator(input_q, output_q),
        consume(output_q)
    )

async def consume(q):
    while True:
        t = await q.get()
        print("📡 Telemetry:", t)

asyncio.run(main())
