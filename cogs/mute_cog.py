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

class TimeoutModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeouts = {}
        self.db_path = "database/moderation"
        os.makedirs(self.db_path, exist_ok=True)
        self.load_timeouts()
        bot.loop.create_task(self.check_timeouts())

    def get_timeout_file_path(self, guild_id: int) -> str:
        """Get the path to the timeout file for a specific guild"""
        return os.path.join(self.db_path, f"{guild_id}_timeouts.json")

    def load_timeouts(self):
        """Load timeouts from JSON files"""
        print(f"{Fore.YELLOW}Loading timeouts from database...")
        for filename in os.listdir(self.db_path):
            if filename.endswith("_timeouts.json"):
                guild_id = int(filename.split("_")[0])
                file_path = os.path.join(self.db_path, filename)
                try:
                    with open(file_path, 'r') as f:
                        guild_timeouts = json.load(f)
                        # Convert string keys back to integers
                        self.timeouts[guild_id] = {
                            int(user_id): expiry_time 
                            for user_id, expiry_time in guild_timeouts.items()
                        }
                    print(f"{Fore.GREEN}Loaded timeouts for guild {guild_id}")
                except Exception as e:
                    print(f"{Fore.RED}Error loading timeouts for guild {guild_id}: {e}")

    def save_guild_timeouts(self, guild_id: int):
        """Save timeouts for a specific guild to JSON"""
        file_path = self.get_timeout_file_path(guild_id)
        try:
            if guild_id in self.timeouts and self.timeouts[guild_id]:
                with open(file_path, 'w') as f:
                    json.dump(self.timeouts[guild_id], f, indent=4)
            else:
                # If no timeouts exist, remove the file if it exists
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"{Fore.RED}Error saving timeouts for guild {guild_id}: {e}")

    async def check_timeouts(self):
        """Background task to check and remove timeouts when they expire"""
        while True:
            current_time = datetime.now().timestamp()
            for guild_id in list(self.timeouts.keys()):
                guild_updated = False
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                for user_id in list(self.timeouts[guild_id].keys()):
                    if self.timeouts[guild_id][user_id] <= current_time:
                        try:
                            # Get member and remove timeout
                            member = guild.get_member(user_id)
                            if member:
                                await member.timeout(None, reason="Timeout duration expired")
                                print(f"{Fore.GREEN}Removed timeout for user {user_id} in guild {guild_id} (timeout expired)")
                            
                            # Remove from timeouts
                            del self.timeouts[guild_id][user_id]
                            guild_updated = True
                            
                        except Exception as e:
                            print(f"{Fore.RED}Error removing timeout for user {user_id}: {e}")
                
                if guild_updated:
                    if not self.timeouts[guild_id]:
                        del self.timeouts[guild_id]
                    self.save_guild_timeouts(guild_id)
            
            await asyncio.sleep(60)  # Check every minute

    @nextcord.slash_command(name="mute", description="[🔇] Timeout/mute a user")
    async def mute(self, interaction, 
                  member: nextcord.Member = SlashOption(required=True), 
                  duration: str = SlashOption(required=True, description="Timeout duration (e.g. 1h, 1d, max 28d)"),
                  reason: str = SlashOption(required=False, default="No reason provided")):
        guild_id = interaction.guild.id
        await interaction.response.defer()
        
        if not interaction.user.guild_permissions.moderate_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to timeout members!")
            return await interaction.followup.send(embed=embed)

        if member.top_role >= interaction.user.top_role:
            embed = create_embed("🚫 Permission Denied", "You cannot timeout members with equal or higher roles!")
            return await interaction.followup.send(embed=embed)

        # Parse duration
        duration_seconds = parse_duration(duration)
        if duration_seconds is None:
            embed = create_embed("❌ Invalid Duration", "Please use a valid duration format (e.g. 1h, 1d)")
            return await interaction.followup.send(embed=embed)

        # Discord has a max timeout duration of 28 days
        if duration_seconds > 28 * 24 * 3600:
            embed = create_embed("❌ Invalid Duration", "Timeout duration cannot exceed 28 days")
            return await interaction.followup.send(embed=embed)
        
        try:
            # Apply timeout
            until = datetime.utcnow() + timedelta(seconds=duration_seconds)
            await member.timeout(until, reason=reason)
            
            # Store timeout
            if guild_id not in self.timeouts:
                self.timeouts[guild_id] = {}
            self.timeouts[guild_id][member.id] = datetime.now().timestamp() + duration_seconds
            self.save_guild_timeouts(guild_id)
            
            # Log the case
            case_manager = self.bot.get_cog('CaseManagementCog')
            if case_manager:
                case_manager.log_case(guild_id, "Timeout", interaction.user.name, member.name, 
                                    f"{reason} | Duration: {duration}")

            embed = create_embed(
                "🔇 User Timed Out", 
                f"{member.mention} has been timed out for {duration}\nReason: {reason}", 
                color=nextcord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
            print(f"{Fore.BLUE}{interaction.user.name} {Fore.GREEN}timed out user {Fore.RED}{member.name}")
            
        except nextcord.Forbidden:
            embed = create_embed("❌ Error", "I don't have permission to timeout this user!")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = create_embed("❌ Error", f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed)

    @nextcord.slash_command(name="unmute", description="[🔊] Remove timeout/unmute a user")
    async def unmute(self, interaction,
                    member: nextcord.Member = SlashOption(required=True),
                    reason: str = SlashOption(required=False, default="No reason provided")):
        guild_id = interaction.guild.id
        await interaction.response.defer()

        if not interaction.user.guild_permissions.moderate_members:
            embed = create_embed("🚫 Permission Denied", "You do not have permission to remove timeouts!")
            return await interaction.followup.send(embed=embed)

        if member.top_role >= interaction.user.top_role:
            embed = create_embed("🚫 Permission Denied", "You cannot modify timeouts for members with equal or higher roles!")
            return await interaction.followup.send(embed=embed)

        try:
            # Remove timeout
            await member.timeout(None, reason=reason)
            
            # Remove from stored timeouts if exists
            if guild_id in self.timeouts and member.id in self.timeouts[guild_id]:
                del self.timeouts[guild_id][member.id]
                if not self.timeouts[guild_id]:
                    del self.timeouts[guild_id]
                self.save_guild_timeouts(guild_id)

            # Log the case
            case_manager = self.bot.get_cog('CaseManagementCog')
            if case_manager:
                case_manager.log_case(guild_id, "Timeout Removed", interaction.user.name, member.name, reason)

            embed = create_embed(
                "🔊 Timeout Removed", 
                f"Timeout has been removed for {member.mention}\nReason: {reason}", 
                color=nextcord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            print(f"{Fore.BLUE}{interaction.user.name} {Fore.GREEN}removed timeout for user {Fore.RED}{member.name}")

        except nextcord.Forbidden:
            embed = create_embed("❌ Error", "I don't have permission to modify this user's timeout!")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = create_embed("❌ Error", f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(TimeoutModerationCog(bot))