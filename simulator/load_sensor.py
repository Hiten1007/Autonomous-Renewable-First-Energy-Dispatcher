import asyncio, random
from datetime import datetime

async def load_sensor(queue):
    while True:
        data = {
            "source": "load",
            "timestamp": datetime.utcnow(),
            "load_kw": round(random.uniform(10, 30), 2)
        }
        await queue.put(data)
        await asyncio.sleep(20)
