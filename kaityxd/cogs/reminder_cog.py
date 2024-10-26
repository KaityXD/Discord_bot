import nextcord
from nextcord.ext import commands, tasks
from typing import List, Dict, Optional, Union
import os
import json
from datetime import datetime, timedelta
import re
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

@dataclass
class Reminder:
    """Data class for storing reminder information."""
    name: str
    time: datetime
    channel_id: Optional[int] = None  # Allow sending to specific channel
    message: str = ""  # Optional custom message
    recurring: bool = False  # Support for recurring reminders
    
    def to_dict(self) -> Dict:
        """Convert reminder to dictionary for JSON storage."""
        return {
            "name": self.name,
            "time": self.time.isoformat(),
            "channel_id": self.channel_id,
            "message": self.message,
            "recurring": self.recurring
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Reminder':
        """Create reminder from dictionary."""
        return cls(
            name=data["name"],
            time=datetime.fromisoformat(data["time"]),
            channel_id=data.get("channel_id"),
            message=data.get("message", ""),
            recurring=data.get("recurring", False)
        )

class ReminderManager:
    """Handles reminder storage and retrieval."""
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_user_file(self, user_id: int) -> Path:
        return self.base_path / f"{user_id}_reminder.json"
    
    def load_reminders(self, user_id: int) -> List[Reminder]:
        try:
            path = self.get_user_file(user_id)
            if not path.exists():
                return []
            with path.open('r') as file:
                data = json.load(file)
                return [Reminder.from_dict(rem) for rem in data]
        except Exception as e:
            logger.error(f"Error loading reminders for user {user_id}: {e}")
            return []
    
    def save_reminders(self, user_id: int, reminders: List[Reminder]) -> bool:
        try:
            path = self.get_user_file(user_id)
            with path.open('w') as file:
                json.dump([rem.to_dict() for rem in reminders], file, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving reminders for user {user_id}: {e}")
            return False

class ReminderCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = ReminderManager('database/reminder')
        self.reminder_check.start()
        
    def parse_duration(self, duration: str) -> Optional[timedelta]:
        """Parse duration strings like '1h30m' or '2d12h' into timedelta."""
        time_pattern = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
        match = time_pattern.fullmatch(duration)
        if not match:
            return None
        
        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        
        if all(x == 0 for x in (days, hours, minutes, seconds)):
            return None
            
        return timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds
        )

    @nextcord.slash_command(name="reminder", description="Manage your reminders")
    async def reminder(self, interaction: nextcord.Interaction):
        pass

    @reminder.subcommand(description="Create a new reminder")
    async def create(
        self,
        interaction: nextcord.Interaction,
        name: str,
        duration: str,
        message: str = "",
        channel: nextcord.TextChannel = None,
        recurring: bool = False
    ):
        """Create a reminder with optional custom message and channel."""
        try:
            delta = self.parse_duration(duration)
            if not delta:
                await interaction.response.send_message(
                    "Invalid duration format! Use combinations like '1d12h30m' or '45s'.",
                    ephemeral=True
                )
                return

            remind_time = datetime.utcnow() + delta
            reminder = Reminder(
                name=name,
                time=remind_time,
                channel_id=channel.id if channel else None,
                message=message,
                recurring=recurring
            )
            
            reminders = self.manager.load_reminders(interaction.user.id)
            reminders.append(reminder)
            
            if self.manager.save_reminders(interaction.user.id, reminders):
                response = f"✅ Reminder '{name}' set for {duration}"
                if channel:
                    response += f" in #{channel.name}"
                if recurring:
                    response += " (recurring)"
                await interaction.response.send_message(response, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to save reminder. Please try again.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating the reminder.",
                ephemeral=True
            )

    @reminder.subcommand(description="List your reminders")
    async def list(self, interaction: nextcord.Interaction):
        """List all active reminders."""
        reminders = self.manager.load_reminders(interaction.user.id)
        
        if not reminders:
            await interaction.response.send_message("You have no active reminders.", ephemeral=True)
            return

        embed = nextcord.Embed(
            title="Your Reminders",
            color=nextcord.Color.blue()
        )
        
        for i, rem in enumerate(reminders, 1):
            time_left = rem.time - datetime.utcnow()
            if time_left.total_seconds() > 0:
                value = f"Due in: {self.format_timedelta(time_left)}\n"
                if rem.channel_id:
                    channel = self.bot.get_channel(rem.channel_id)
                    value += f"Channel: #{channel.name if channel else 'unknown'}\n"
                if rem.message:
                    value += f"Message: {rem.message}\n"
                if rem.recurring:
                    value += "🔄 Recurring"
                
                embed.add_field(
                    name=f"{i}. {rem.name}",
                    value=value.strip(),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @reminder.subcommand(description="Delete a specific reminder")
    async def delete(self, interaction: nextcord.Interaction, reminder_number: int):
        """Delete a specific reminder by its number from the list."""
        reminders = self.manager.load_reminders(interaction.user.id)
        
        if not reminders:
            await interaction.response.send_message("You have no reminders to delete.", ephemeral=True)
            return
            
        if not 1 <= reminder_number <= len(reminders):
            await interaction.response.send_message(
                f"Invalid reminder number. Please use /reminder list to see valid numbers.",
                ephemeral=True
            )
            return
            
        deleted_reminder = reminders.pop(reminder_number - 1)
        if self.manager.save_reminders(interaction.user.id, reminders):
            await interaction.response.send_message(
                f"✅ Deleted reminder: {deleted_reminder.name}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to delete reminder. Please try again.",
                ephemeral=True
            )

    @reminder.subcommand(description="Clear all reminders")
    async def clear(self, interaction: nextcord.Interaction):
        """Clear all reminders for the user."""
        path = self.manager.get_user_file(interaction.user.id)
        try:
            if path.exists():
                path.unlink()
                await interaction.response.send_message("✅ All reminders cleared.", ephemeral=True)
            else:
                await interaction.response.send_message("You have no reminders to clear.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error clearing reminders: {e}")
            await interaction.response.send_message(
                "❌ Failed to clear reminders. Please try again.",
                ephemeral=True
            )

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        """Check and process due reminders."""
        try:
            for user_file in self.manager.base_path.glob('*_reminder.json'):
                user_id = int(user_file.stem.split('_')[0])
                reminders = self.manager.load_reminders(user_id)
                new_reminders = []
                current_time = datetime.utcnow()

                for reminder in reminders:
                    if current_time >= reminder.time:
                        try:
                            await self.send_reminder(user_id, reminder)
                            if reminder.recurring:
                                # Add next occurrence for recurring reminders
                                reminder.time = current_time + timedelta(days=1)
                                new_reminders.append(reminder)
                        except Exception as e:
                            logger.error(f"Error sending reminder: {e}")
                    else:
                        new_reminders.append(reminder)

                self.manager.save_reminders(user_id, new_reminders)
        except Exception as e:
            logger.error(f"Error in reminder check loop: {e}")

    async def send_reminder(self, user_id: int, reminder: Reminder):
        """Send a reminder to the user or specified channel."""
        try:
            if reminder.channel_id:
                channel = self.bot.get_channel(reminder.channel_id)
                if channel:
                    await channel.send(
                        f"⏰ <@{user_id}> Reminder: {reminder.name}\n{reminder.message}"
                    )
                    return
            
            user = await self.bot.fetch_user(user_id)
            if user:
                message = f"⏰ Reminder: {reminder.name}"
                if reminder.message:
                    message += f"\n{reminder.message}"
                await user.send(message)
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")

    @reminder_check.before_loop
    async def before_reminder_check(self):
        """Wait for the bot to be ready before starting the reminder check loop."""
        await self.bot.wait_until_ready()

    @staticmethod
    def format_timedelta(td: timedelta) -> str:
        """Format a timedelta into a human-readable string."""
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds and not (days or hours):
            parts.append(f"{seconds}s")
            
        return " ".join(parts) if parts else "now"

def setup(bot: commands.Bot):
    bot.add_cog(ReminderCog(bot))