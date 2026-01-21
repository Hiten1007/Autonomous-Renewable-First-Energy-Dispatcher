import asyncio, random
from datetime import datetime

async def solar_sensor(queue):
    while True:
        data = {
            "source": "solar",
            "timestamp": datetime.utcnow(),
            "solar_kw": round(random.uniform(5, 20), 2),
            "battery_soc": round(random.uniform(0.3, 0.9), 2)
        }
        await queue.put(data)
        await asyncio.sleep(45)
