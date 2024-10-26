import nextcord
from nextcord import Interaction
from nextcord.ext import commands
import psutil
import platform

class SystemInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="systeminfo", description="[💻] Show the system information of the bot")
    async def systeminfo(self, interaction: Interaction):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        system = platform.system()
        release = platform.release()

        total_memory_mb = memory.total / (1024 ** 2)  # Total memory in MB
        used_memory_mb = memory.used / (1024 ** 2)    # Used memory in MB
        available_memory_mb = memory.available / (1024 ** 2)  # Available memory in MB

        embed = nextcord.Embed(
            title="📊 System Information",
            description="Information about the bot's system performance",
            color=nextcord.Color.green()
        )

        embed.add_field(name="🖥️ Operating System", value=f"{system} {release}", inline=False)
        embed.add_field(name="💾 RAM Usage", value=f"{memory.percent}%", inline=True)
        embed.add_field(name="📏 Total RAM", value=f"{total_memory_mb:.2f} MB", inline=True)
        embed.add_field(name="📦 Used RAM", value=f"{used_memory_mb:.2f} MB", inline=True)
        embed.add_field(name="📥 Available RAM", value=f"{available_memory_mb:.2f} MB", inline=True)
        embed.add_field(name="💽 Disk Usage", value=f"{disk.percent}%", inline=True)
        embed.add_field(name="🧠 CPU Usage", value=f"{cpu_percent}%", inline=True)

        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(SystemInfo(bot))
