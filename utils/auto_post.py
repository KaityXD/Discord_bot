import asyncio
from typing import Dict
import random
import httpx
from nextcord.ext import tasks
from nextcord import Embed

class AutoPostManager:
    def __init__(self, bot):
        self.bot = bot
        self.auto_post_tasks: Dict[int, tasks.Loop] = {}
        self.categories = [
            "waifu", "neko", "shinobu", "megumin", 
            "cuddle", "cry", "hug", "kiss", "pat",
            "smug", "bonk", "blush", "smile",
            "wave", "highfive", "handhold", "nom",
            "bite", "slap", "happy", "wink", 
            "poke", "dance", "cringe"
        ]
        self.api_url = "https://api.waifu.pics/sfw/"
        self.api_nsfw = "https://api.waifu.pics/nsfw/"

    async def fetch_image(self, category):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}{category}")
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            return None

    async def fetch_image_nsfw(self, category):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_nsfw}{category}")
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            return None

    def create_auto_post_task(self, guild_id: int, channel_id: int, interval: int):
        """Creates a new auto-post task for a guild"""
        @tasks.loop(minutes=interval)
        async def auto_post_task():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                print(f"Channel {channel_id} not found for guild {guild_id}")
                return

            try:
                category = random.choice(self.categories)
                image_url = await self.fetch_image(category)
                
                if image_url:
                    embed = Embed(
                        title=f"Auto Post: {category.title()} Image",
                        color=0xff69b4
                    )
                    embed.set_image(url=image_url)
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Error in auto-post task for guild {guild_id}: {e}")

        return auto_post_task

    def start_task(self, guild_id: int, channel_id: int, interval: int):
        """Starts or restarts an auto-post task for a guild"""
        # Stop existing task if it exists
        self.stop_task(guild_id)

        # Create and start new task
        task = self.create_auto_post_task(guild_id, channel_id, interval)
        task.start()
        self.auto_post_tasks[guild_id] = task

    def stop_task(self, guild_id: int):
        """Stops an auto-post task for a guild"""
        if guild_id in self.auto_post_tasks:
            self.auto_post_tasks[guild_id].cancel()
            del self.auto_post_tasks[guild_id]

    def stop_all_tasks(self):
        """Stops all auto-post tasks"""
        for task in self.auto_post_tasks.values():
            task.cancel()
        self.auto_post_tasks.clear()
