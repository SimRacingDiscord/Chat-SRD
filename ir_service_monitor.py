import aiohttp
from discord_webhook import DiscordWebhook
import asyncio
import logging

# Setup Logging
logger = logging.getLogger("chatsrd_irservicemonitor_log")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("chat_srd_irservicemonitor.log", encoding="utf-8", mode="a")
print(f"Log file created at: {handler.baseFilename}")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class ir_service_monitor:
    def __init__(self, webhook_url):
        self.maintenance_message = []
        self.status_url = "https://status.iracing.com/status.json"
        self.webhook_url = webhook_url

    async def fetch_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.status_url) as response:
                return await response.json()
            
    async def check_status(self):
        status = await self.fetch_status()
        for service in status:
            if service[1][1] == 0:
                message = f"{service[0]} is down. {service[1][0]}"
            else:
                message = f"{service[0]} is up."

            webhook = DiscordWebhook(url=self.webhook_url, content=message)
            webhook.execute()
        return status

webhook_url = 'https://discord.com/api/webhooks/1134726152150331442/g_DeNqVdYBLUCrhovxULDxCKECvYs3hXO8lIscDRB9tv6hoi8M0uy8OV5eAWFQf7r2wI'


async def monitor():
    maintenance_message = []
    while True:
        status = await service_monitor.fetch_status()
        if status["maint_messages"] != maintenance_message:
            maintenance_message = [status["maint_messages"]]
            message = f"iRacing Maintenance Update: {maintenance_message}"
            webhook = DiscordWebhook(url=webhook_url, content=message)
            webhook.execute()
           
        else:

            logger.info("iRacing Service Monitor: No new maintenance messages.")
        await asyncio.sleep(60)

# Run the monitor function indefinitely
#asyncio.run(monitor())
