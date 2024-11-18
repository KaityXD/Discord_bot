import nextcord
from nextcord.ext import commands
from utils.music_utils import create_embed
import json
import os
from datetime import datetime
import re

def parse_duration(duration_str):
    if not duration_str:
        return None

    pattern = r'(\d+)([smhdwMy])'
    matches = re.findall(pattern, duration_str.lower())
    
    if not matches:
        return None

    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 's':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
        elif unit == 'w':
            total_seconds += value * 604800
        elif unit == 'M':
            total_seconds += value * 2629746
        elif unit == 'y':
            total_seconds += value * 31556952

    return total_seconds

class CaseManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cases = {}
        self.config = {}
        self.load_data()

    def load_data(self):
        os.makedirs("database/moderator", exist_ok=True)
        
        cases_path = "database/moderator/cases.json"
        if os.path.exists(cases_path):
            with open(cases_path, "r") as f:
                self.cases = json.load(f)
                
        config_path = "database/moderator/config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)

    def save_cases(self):
        with open("database/moderator/cases.json", "w") as f:
            json.dump(self.cases, f, indent=4)

    def save_config(self):
        with open("database/moderator/config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def log_case(self, guild_id, case_type, moderator, member, reason):
        guild_id = str(guild_id)
        if guild_id not in self.cases:
            self.cases[guild_id] = {}

        case_id = str(len(self.cases[guild_id]) + 1)
        case_info = {
            "type": case_type,
            "moderator": moderator,
            "member": member,
            "reason": reason,
            "verdict": "Pending review",
            "notes": "",
            "timestamp": datetime.now().isoformat()
        }
        self.cases[guild_id][case_id] = case_info
        self.save_cases()
        
        self.bot.loop.create_task(self.send_case_log(guild_id, case_id, case_info))

    async def send_case_log(self, guild_id, case_id, case_info):
        if guild_id not in self.config:
            return
            
        channel_id = self.config[guild_id].get("mod_channel_id")
        if channel_id:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                embed = create_embed(
                    f"🗂️ Case ID: {case_id}",
                    f"**Type:** {case_info['type']}\n"
                    f"**Moderator:** {case_info['moderator']}\n"
                    f"**Member:** {case_info['member']}\n"
                    f"**Reason:** {case_info['reason']}\n"
                    f"**Verdict:** {case_info['verdict']}\n"
                    f"**Notes:** {case_info['notes']}\n"
                    f"**Timestamp:** {case_info['timestamp']}",
                    nextcord.Color.blue()
                )
                await channel.send(embed=embed)

    @nextcord.slash_command(name="case", description="[🛡️] View a specific case by ID")
    async def view_case(self, interaction: nextcord.Interaction, case_id: str):
        if not interaction.user.guild_permissions.manage_messages:
            embed = create_embed("🚫 Permission Denied", 
                               "You need Manage Messages permission to view cases!", 
                               nextcord.Color.red())
            return await interaction.send(embed=embed, ephemeral=True)

        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.cases:
            embed = create_embed("❌ Error", 
                               "No cases found for this server.", 
                               nextcord.Color.red())
            return await interaction.send(embed=embed, ephemeral=True)
            
        if case_id not in self.cases[guild_id]:
            embed = create_embed("❌ Error", 
                               f"Case #{case_id} not found.", 
                               nextcord.Color.red())
            return await interaction.send(embed=embed, ephemeral=True)
            
        case_info = self.cases[guild_id][case_id]
        embed = create_embed(
            f"🗂️ Case #{case_id}",
            f"**Type:** {case_info['type']}\n"
            f"**Moderator:** {case_info['moderator']}\n"
            f"**Member:** {case_info['member']}\n"
            f"**Reason:** {case_info['reason']}\n"
            f"**Verdict:** {case_info['verdict']}\n"
            f"**Notes:** {case_info['notes']}\n"
            f"**Timestamp:** {case_info['timestamp']}",
            nextcord.Color.blue()
        )
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="set_mod_channel", description="[🛡️] Set the channel where moderation logs are sent")
    async def set_mod_channel(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            embed = create_embed("🚫 Permission Denied", 
                               "You do not have permission to use this command!", 
                               nextcord.Color.red())
            return await interaction.send(embed=embed)

        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]["mod_channel_id"] = channel.id
        self.save_config()
        
        embed = create_embed("✅ Mod Channel Set", 
                           f"Moderation logs will be sent to {channel.mention}.", 
                           nextcord.Color.green())
        await interaction.send(embed=embed)

def setup(bot):
    bot.add_cog(CaseManagementCog(bot))