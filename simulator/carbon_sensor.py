import asyncio, random
from datetime import datetime

async def carbon_sensor(queue):
    while True:
        data = {
            "source": "carbon",
            "timestamp": datetime.utcnow(),
            "grid_carbon_intensity": random.randint(400, 800)
        }
        await queue.put(data)
        await asyncio.sleep(300)  # 5 min
