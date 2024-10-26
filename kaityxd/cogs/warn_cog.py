import nextcord
from nextcord.ext import commands
from utils.music_utils import create_embed
import json
import os
from datetime import datetime

class WarningSystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}
        self.load_warnings()

    def load_warnings(self):
        warning_path = "database/moderator/warnings.json"
        os.makedirs(os.path.dirname(warning_path), exist_ok=True)
        if os.path.exists(warning_path):
            with open(warning_path, "r") as f:
                self.warnings = json.load(f)

    def save_warnings(self):
        warning_path = "database/moderator/warnings.json"
        with open(warning_path, "w") as f:
            json.dump(self.warnings, f, indent=4)

    @nextcord.slash_command(name="warn", description="[🛡️] Warn a user with a reason")
    async def warn(self, interaction: nextcord.Interaction, 
                  member: nextcord.Member, 
                  reason: str):
        guild_id = str(interaction.guild.id)
        member_id = str(member.id)

        if not interaction.user.guild_permissions.kick_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to use this command!")
            return await interaction.send(embed=embed)

        # Initialize guild and member in warnings if they don't exist
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if member_id not in self.warnings[guild_id]:
            self.warnings[guild_id][member_id] = []

        # Add warning
        warning_data = {
            "reason": reason,
            "moderator": interaction.user.name,
            "timestamp": datetime.now().isoformat()
        }
        self.warnings[guild_id][member_id].append(warning_data)
        self.save_warnings()

        # Log the case
        case_manager = self.bot.get_cog('CaseManagementCog')
        if case_manager:
            case_manager.log_case(guild_id, "Warn", interaction.user.name, member.name, reason)

        warning_count = len(self.warnings[guild_id][member_id])
        embed = create_embed(
            "⚠️ User Warned", 
            f"{member.mention} has been warned for: {reason}\nTotal warnings: {warning_count}", 
            nextcord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

        # Auto-kick after 3 warnings
        if warning_count >= 3:
            try:
                await member.kick(reason="Exceeded 3 warnings")
                kick_embed = create_embed(
                    "🦶 User Kicked", 
                    f"{member.mention} has been kicked after receiving 3 warnings", 
                    nextcord.Color.red()
                )
                await interaction.followup.send(embed=kick_embed)
            except nextcord.Forbidden:
                error_embed = create_embed(
                    "❌ Error", 
                    "I don't have permission to kick this user.", 
                    nextcord.Color.red()
                )
                await interaction.followup.send(embed=error_embed)

    @nextcord.slash_command(name="warnings", description="[🛡️] Check warnings for a user")
    async def warnings(self, interaction: nextcord.Interaction, member: nextcord.Member):
        guild_id = str(interaction.guild.id)
        member_id = str(member.id)

        if not interaction.user.guild_permissions.kick_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to use this command!")
            return await interaction.send(embed=embed)

        if guild_id not in self.warnings or member_id not in self.warnings[guild_id]:
            embed = create_embed("📝 Warnings", f"{member.mention} has no warnings.", nextcord.Color.green())
            return await interaction.send(embed=embed)

        warning_list = self.warnings[guild_id][member_id]
        warning_text = "\n\n".join([
            f"Warning {i+1}:\nReason: {w['reason']}\nModerator: {w['moderator']}\nDate: {w['timestamp']}"
            for i, w in enumerate(warning_list)
        ])

        embed = create_embed(
            f"📝 Warnings for {member.name}",
            f"Total warnings: {len(warning_list)}\n\n{warning_text}",
            nextcord.Color.yellow()
        )
        await interaction.send(embed=embed)

def setup(bot):
    bot.add_cog(WarningSystemCog(bot))