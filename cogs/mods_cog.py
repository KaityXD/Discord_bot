import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
from utils.music_utils import create_embed
from datetime import datetime, timedelta
import json
import os
import asyncio
from colorama import Fore

def parse_duration(duration_str: str) -> int:
    """Convert duration string to seconds"""
    try:
        unit = duration_str[-1].lower()
        value = int(duration_str[:-1])
        
        units = {
            's': 1,               # seconds
            'm': 60,             # minutes
            'h': 3600,           # hours
            'd': 86400,          # days
            'w': 604800,         # weeks
            'M': 2592000         # months (30 days)
        }
        
        if unit not in units:
            return None
            
        return value * units[unit]
    except (ValueError, IndexError):
        return None

class BasicModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_bans = {}
        self.db_path = "database/moderator"
        os.makedirs(self.db_path, exist_ok=True)
        self.load_temp_bans()
        bot.loop.create_task(self.check_temp_bans())

    def get_ban_file_path(self, guild_id: int) -> str:
        """Get the path to the ban file for a specific guild"""
        return os.path.join(self.db_path, f"{guild_id}_bans.json")

    def load_temp_bans(self):
        """Load temporary bans from JSON files"""
        print(f"{Fore.YELLOW}Loading temporary bans from database...")
        for filename in os.listdir(self.db_path):
            if filename.endswith("_bans.json"):
                guild_id = int(filename.split("_")[0])
                file_path = os.path.join(self.db_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        guild_bans = json.load(f)
                        # Convert string keys back to integers
                        self.temp_bans[guild_id] = {
                            int(user_id): expiry_time 
                            for user_id, expiry_time in guild_bans.items()
                        }
                    print(f"{Fore.GREEN}Loaded bans for guild {guild_id}")
                except Exception as e:
                    print(f"{Fore.RED}Error loading bans for guild {guild_id}: {e}")

    def save_guild_bans(self, guild_id: int):
        """Save temporary bans for a specific guild to JSON"""
        file_path = self.get_ban_file_path(guild_id)
        try:
            if guild_id in self.temp_bans and self.temp_bans[guild_id]:
                with open(file_path, 'w') as f:
                    json.dump(self.temp_bans[guild_id], f, indent=4)
            else:
                # If no bans exist, remove the file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"{Fore.RED}Error saving bans for guild {guild_id}: {e}")

    async def check_temp_bans(self):
        """Background task to check and unban users when their ban duration expires"""
        while True:
            current_time = datetime.now().timestamp()
            for guild_id in list(self.temp_bans.keys()):
                guild_updated = False
                for user_id in list(self.temp_bans[guild_id].keys()):
                    if self.temp_bans[guild_id][user_id] <= current_time:
                        # Time to unban
                        try:
                            guild = self.bot.get_guild(guild_id)
                            if guild:
                                await guild.unban(nextcord.Object(id=user_id), reason="Temporary ban expired")
                                print(f"{Fore.GREEN}Unbanned user {user_id} from guild {guild_id} (ban expired)")
                            
                            # Remove from temp bans
                            del self.temp_bans[guild_id][user_id]
                            guild_updated = True
                            
                        except Exception as e:
                            print(f"{Fore.RED}Error unbanning user {user_id}: {e}")
                
                if guild_updated:
                    if not self.temp_bans[guild_id]:
                        del self.temp_bans[guild_id]
                    self.save_guild_bans(guild_id)
            
            await asyncio.sleep(60)  # Check every minute

    @nextcord.slash_command(name="ban", description="[🛡️] Ban a user from the server")
    async def ban(self, interaction, 
                 member: nextcord.Member = SlashOption(required=True), 
                 reason: str = SlashOption(required=False, default="No reason provided"),
                 duration: str = SlashOption(required=False, description="Ban duration (e.g. 1d, 1w, 1M)")):
        guild_id = interaction.guild.id
        await interaction.response.defer()
        
        if not interaction.user.guild_permissions.ban_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to use this command!")
            return await interaction.followup.send(embed=embed)

        if member.top_role >= interaction.user.top_role:
            embed = create_embed("🚫 Permission Denied", "You cannot ban members with equal or higher roles!")
            return await interaction.followup.send(embed=embed)

        # Parse duration if provided
        duration_seconds = None
        if duration:
            duration_seconds = parse_duration(duration)
            if duration_seconds is None:
                embed = create_embed("❌ Invalid Duration", "Please use a valid duration format (e.g. 1d, 1w, 1M)")
                return await interaction.followup.send(embed=embed)
        
        try:
            await member.ban(reason=reason)
            
            # Handle temporary ban
            if duration_seconds:
                if guild_id not in self.temp_bans:
                    self.temp_bans[guild_id] = {}
                self.temp_bans[guild_id][member.id] = datetime.now().timestamp() + duration_seconds
                self.save_guild_bans(guild_id)
            
            # Log the case
            case_manager = self.bot.get_cog('CaseManagementCog')
            if case_manager:
                case_manager.log_case(guild_id, "Ban", interaction.user.name, member.name, 
                                    f"{reason} | Duration: {duration if duration else 'Permanent'}")

            duration_text = f" for {duration}" if duration else " permanently"
            embed = create_embed(
                f"❌ User Banned", 
                f"{member.mention} has been banned{duration_text}\nReason: {reason}", 
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            print(f"{Fore.BLUE}{interaction.user.name} {Fore.GREEN}banned user {Fore.RED}{member.name}")
            
        except nextcord.Forbidden:
            embed = create_embed("❌ Error", "I don't have permission to ban this user!")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = create_embed("❌ Error", f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed)

    @nextcord.slash_command(name="kick", description="[🛡️] Kick a user from the server")
    async def kick(self, interaction, 
                  member: nextcord.Member = SlashOption(required=True), 
                  reason: str = SlashOption(required=False, default="No reason provided")):
        guild_id = interaction.guild.id
        await interaction.response.defer()
        
        if not interaction.user.guild_permissions.kick_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to use this command!")
            return await interaction.followup.send(embed=embed)

        if member.top_role >= interaction.user.top_role:
            embed = create_embed("🚫 Permission Denied", "You cannot kick members with equal or higher roles!")
            return await interaction.followup.send(embed=embed)

        try:
            await member.kick(reason=reason)
            
            # Log the case
            case_manager = self.bot.get_cog('CaseManagementCog')
            if case_manager:
                case_manager.log_case(guild_id, "Kick", interaction.user.name, member.name, reason)

            embed = create_embed(
                "🦶 User Kicked", 
                f"{member.mention} has been kicked from the server\nReason: {reason}", 
                color=nextcord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            print(f"{Fore.BLUE}{interaction.user.name} {Fore.GREEN}kicked user {Fore.RED}{member.name}")
            
        except nextcord.Forbidden:
            embed = create_embed("❌ Error", "I don't have permission to kick this user!")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = create_embed("❌ Error", f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(BasicModerationCog(bot))