import nextcord
from nextcord.ext import commands
from nextcord import Embed, SlashOption
import json
import os
from utils.auto_post import AutoPostManager
import random

class WaifuSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_path = "database/waifu/guild_settings.json"
        self.categories = [
            "waifu", "neko", "shinobu", "megumin", 
            "cuddle", "cry", "hug", "kiss", "pat",
            "smug", "bonk", "blush", "smile",
            "wave", "highfive", "handhold", "nom",
            "bite", "slap", "happy", "wink", 
            "poke", "dance", "cringe"
        ]
        self.auto_poster = AutoPostManager(bot)
        self.load_settings()
        self.start_auto_posts()

    def load_settings(self):
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        if not os.path.exists(self.settings_path):
            with open(self.settings_path, 'w') as f:
                json.dump({}, f, indent=4)

    def get_guild_settings(self, guild_id: int) -> dict:
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {})
        except:
            return {}

    def save_guild_settings(self, guild_id: int, settings: dict):
        try:
            with open(self.settings_path, 'r') as f:
                all_settings = json.load(f)
        except:
            all_settings = {}

        if settings:  
            all_settings[str(guild_id)] = settings
        else:
            all_settings.pop(str(guild_id), None)
        
        with open(self.settings_path, 'w') as f:
            json.dump(all_settings, f, indent=4)

        if settings.get('auto_post'):
            self.auto_poster.start_task(
                guild_id, 
                settings['channel_id'], 
                settings.get('interval', 60)
            )
        else:
            self.auto_poster.stop_task(guild_id)

    def start_auto_posts(self):
        try:
            with open(self.settings_path, 'r') as f:
                all_settings = json.load(f)
                
            for guild_id_str, settings in all_settings.items():
                if settings.get('auto_post') and settings.get('channel_id'):
                    channel = self.bot.get_channel(settings['channel_id'])
                    guild_id = int(guild_id_str)
                    if not channel:
                        settings_copy = settings.copy()
                        settings_copy['auto_post'] = False
                        self.save_guild_settings(guild_id, settings_copy)
                        continue
                        
                    self.auto_poster.start_task(
                        guild_id,
                        settings['channel_id'],
                        settings.get('interval', 60)
                    )
        except Exception as e:
            pass

    def cog_unload(self):
        self.auto_poster.stop_all_tasks()

    @nextcord.slash_command(
        name="waifu",
        description="Get waifu images!"
    )
    async def waifu(
        self,
        interaction: nextcord.Interaction,
        category: str = SlashOption(
            name="category",
            description="Choose a category",
            required=False,
            choices=["random"] + sorted(["waifu", "neko", "shinobu", "megumin", 
                "cuddle", "cry", "hug", "kiss", "pat", "smug", "bonk", 
                "blush", "smile", "wave", "highfive", "handhold", "nom", 
                "bite", "slap", "happy", "wink", "poke", "dance", "cringe"])
        )
    ):
        await interaction.response.defer()

        if not category:
            embed = Embed(
                title="Waifu Commands",
                description="Choose a category from the dropdown menu!",
                color=0xff69b4
            )
            categories_text = "`, `".join(self.categories)
            embed.add_field(name="Available Categories", value=f"`{categories_text}`")
            await interaction.followup.send(embed=embed)
            return

        if category == "random":
            category = random.choice(self.categories)

        image_url = await self.auto_poster.fetch_image(category)
        if image_url:
            embed = Embed(
                title=f"{category.title()} Image",
                color=0xff69b4
            )
            embed.set_image(url=image_url)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Failed to fetch image. Please try again!")

    @nextcord.slash_command(
        name="waifusetup",
        description="Configure waifu settings for the server",
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def waifu_setup(
        self,
        interaction: nextcord.Interaction,
        channel: nextcord.TextChannel = SlashOption(
            name="channel",
            description="Channel for waifu images",
            required=True
        ),
        auto_post: bool = SlashOption(
            name="auto_post",
            description="Enable automatic posting",
            required=False,
            default=False
        ),
        interval: int = SlashOption(
            name="interval",
            description="Minutes between auto posts (if enabled)",
            required=False,
            min_value=1,
            max_value=1440,
            default=60
        )
    ):
        settings = {
            "channel_id": channel.id,
            "auto_post": auto_post,
            "interval": interval
        }
        
        self.save_guild_settings(interaction.guild_id, settings)
        
        status = "enabled" if auto_post else "disabled"
        embed = Embed(
            title="Waifu Settings Updated",
            description=f"Channel: {channel.mention}\nAuto Post: {status}\nInterval: {interval} minutes",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="waifusettings",
        description="View current waifu settings"
    )
    async def waifu_settings(self, interaction: nextcord.Interaction):
        settings = self.get_guild_settings(interaction.guild_id)
        
        if not settings:
            await interaction.response.send_message("No settings configured! Use `/waifusetup` first.")
            return
            
        channel = self.bot.get_channel(settings.get("channel_id"))
        if not channel:
            settings_copy = settings.copy()
            settings_copy['auto_post'] = False
            self.save_guild_settings(interaction.guild_id, settings_copy)
            await interaction.response.send_message("Channel not found. Auto-posting has been disabled. Please use `/waifusetup` to set a new channel.")
            return

        status = "enabled" if settings.get('auto_post', False) else "disabled"
        embed = Embed(
            title="Waifu Settings",
            description=(
                f"Channel: {channel.mention}\n"
                f"Auto Post: {status}\n"
                f"Interval: {settings.get('interval', 60)} minutes"
            ),
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(
        name="waifureset",
        description="Reset waifu settings",
        default_member_permissions=nextcord.Permissions(administrator=True)
    )
    async def waifu_reset(self, interaction: nextcord.Interaction):
        self.auto_poster.stop_task(interaction.guild_id)
        self.save_guild_settings(interaction.guild_id, {})
        await interaction.response.send_message("Waifu settings have been reset!")

def setup(bot):
    bot.add_cog(WaifuSlash(bot))