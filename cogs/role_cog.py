import nextcord
from nextcord.ext import commands
from nextcord import slash_command, SlashOption
import asyncio
from datetime import datetime, timedelta
import re

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temporary_roles = {}

    def parse_duration(self, duration_str: str) -> int:
        if not duration_str:
            return 0
        
        time_units = {
            'd': 86400,
            'h': 3600,
            'm': 60,
            's': 1
        }
        
        pattern = r'(\d+)([dhms])'
        matches = re.finditer(pattern, duration_str.lower())
        
        total_seconds = 0
        found_match = False
        
        for match in matches:
            found_match = True
            value, unit = match.groups()
            total_seconds += int(value) * time_units[unit]
        
        if not found_match:
            raise ValueError("Invalid duration format. Use format: 1d12h, 2h30m, etc.")
            
        if total_seconds <= 0:
            raise ValueError("Duration must be positive")
            
        return total_seconds

    def format_duration(self, seconds: int) -> str:
        if seconds == 0:
            return "0 seconds"
            
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts)

    async def remove_role_after_duration(self, member: nextcord.Member, role: nextcord.Role, duration: int):
        await asyncio.sleep(duration)
        if member.id in self.temporary_roles and role.id in self.temporary_roles[member.id]:
            try:
                await member.remove_roles(role)
                del self.temporary_roles[member.id][role.id]
                if not self.temporary_roles[member.id]:
                    del self.temporary_roles[member.id]
            except Exception:
                pass

    def create_error_embed(self, error_message: str) -> nextcord.Embed:
        embed = nextcord.Embed(
            title="❌ Error",
            description=error_message,
            color=0xFF0000
        )
        embed.set_footer(text=f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    def create_success_embed(self, title: str, description: str) -> nextcord.Embed:
        embed = nextcord.Embed(
            title=f"✅ {title}",
            description=description,
            color=0x00FF00
        )
        embed.set_footer(text=f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    @slash_command(name="role", description="[🗣️] Manage roles in the server")
    async def role(self, interaction: nextcord.Interaction):
        pass

    @role.subcommand(name="give", description="[🗣️] Give a role to a user")
    async def give_role(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(name="user", description="The user to give the role to"),
        role: nextcord.Role = SlashOption(name="role", description="The role to give"),
        duration: str = SlashOption(
            name="duration",
            description="Duration (e.g., 1d12h, 2h30m). Leave empty for permanent",
            required=False,
            default=None
        )
    ):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=self.create_error_embed("You do not have permission to manage roles."),
                ephemeral=True
            )
            return

        try:
            if role >= interaction.guild.me.top_role:
                await interaction.response.send_message(
                    embed=self.create_error_embed("I cannot assign roles higher than or equal to my highest role."),
                    ephemeral=True
                )
                return

            if role in member.roles:
                await interaction.response.send_message(
                    embed=self.create_error_embed(f"{member.mention} already has the {role.mention} role."),
                    ephemeral=True
                )
                return

            await member.add_roles(role)

            if duration:
                try:
                    duration_seconds = self.parse_duration(duration)
                    duration_text = self.format_duration(duration_seconds)

                    if member.id not in self.temporary_roles:
                        self.temporary_roles[member.id] = {}
                    self.temporary_roles[member.id][role.id] = datetime.now() + timedelta(seconds=duration_seconds)

                    self.bot.loop.create_task(self.remove_role_after_duration(member, role, duration_seconds))

                    removal_time = datetime.now() + timedelta(seconds=duration_seconds)
                    embed = self.create_success_embed(
                        "Role Added",
                        f"👤 **User:** {member.mention}\n"
                        f"🎭 **Role:** {role.mention}\n"
                        f"⏱️ **Duration:** {duration_text}\n"
                        f"🕒 **Expires:** {removal_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    await interaction.response.send_message(embed=embed)

                except ValueError as e:
                    await interaction.response.send_message(
                        embed=self.create_error_embed(f"Error with duration: {str(e)}"),
                        ephemeral=True
                    )
            else:
                embed = self.create_success_embed(
                    "Role Added",
                    f"👤 **User:** {member.mention}\n"
                    f"🎭 **Role:** {role.mention}\n"
                    f"⏱️ **Duration:** Permanent"
                )
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=self.create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

    @role.subcommand(name="create", description="[🗣️] Create a new role")
    async def create_role(
        self,
        interaction: nextcord.Interaction,
        name: str = SlashOption(name="name", description="The name of the role"),
        color: str = SlashOption(name="color", description="The color of the role (hex code)", required=False),
        hoist: bool = SlashOption(name="hoist", description="Should the role be displayed separately?", required=False, default=False),
        mentionable: bool = SlashOption(name="mentionable", description="Can the role be mentioned?", required=False, default=False)
    ):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=self.create_error_embed("You do not have permission to manage roles."),
                ephemeral=True
            )
            return

        try:
            role_color = nextcord.Color(int(color.strip('#'), 16)) if color else nextcord.Color.default()
            new_role = await interaction.guild.create_role(name=name, color=role_color, hoist=hoist, mentionable=mentionable)
            
            embed = self.create_success_embed(
                "Role Created",
                f"🎭 **Role:** {new_role.mention}\n"
                f"🎨 **Color:** {color if color else 'Default'}\n"
                f"📊 **Hoisted:** {hoist}\n"
                f"💬 **Mentionable:** {mentionable}"
            )
            embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=self.create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

    @role.subcommand(name="modify", description="[🗣️] Modify an existing role")
    async def modify_role(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = SlashOption(name="role", description="The role to modify"),
        name: str = SlashOption(name="new_name", description="New name for the role", required=False),
        color: str = SlashOption(name="new_color", description="New color for the role (hex code)", required=False),
        hoist: bool = SlashOption(name="hoist", description="Should the role be displayed separately?", required=False),
        mentionable: bool = SlashOption(name="mentionable", description="Can the role be mentioned?", required=False)
    ):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=self.create_error_embed("You do not have permission to manage roles."),
                ephemeral=True
            )
            return

        try:
            changes = []
            if name:
                old_name = role.name
                await role.edit(name=name)
                changes.append(f"Name: {old_name} → {name}")
            if color:
                role_color = nextcord.Color(int(color.strip('#'), 16))
                await role.edit(color=role_color)
                changes.append(f"Color: {color}")
            if hoist is not None:
                await role.edit(hoist=hoist)
                changes.append(f"Hoisted: {hoist}")
            if mentionable is not None:
                await role.edit(mentionable=mentionable)
                changes.append(f"Mentionable: {mentionable}")

            embed = self.create_success_embed(
                "Role Modified",
                f"🎭 **Role:** {role.mention}\n"
                f"📝 **Changes:**\n" + '\n'.join(f"• {change}" for change in changes)
            )
            embed.add_field(name="Modified by", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=self.create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

    @role.subcommand(name="delete", description="[🗣️] Delete an existing role")
    async def delete_role(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = SlashOption(name="role", description="The role to delete")
    ):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                embed=self.create_error_embed("You do not have permission to manage roles."),
                ephemeral=True
            )
            return

        try:
            role_name = role.name
            await role.delete()
            
            embed = self.create_success_embed(
                "Role Deleted",
                f"🎭 **Role Name:** {role_name}"
            )
            embed.add_field(name="Deleted by", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                embed=self.create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(RoleManagement(bot))