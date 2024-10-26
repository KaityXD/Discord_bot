import json
import nextcord
from nextcord.ext import commands
from nextcord import Embed
from datetime import datetime
import os

class LoggingListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, guild_id: int) -> dict:
        path = f"database/mod_logs/{guild_id}.json"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"enabled": False, "log_channel": None, "log_types": {}}

    def get_log_channel(self, guild, config):
        log_channel_id = config.get("log_channel")
        return guild.get_channel(log_channel_id) if log_channel_id else None

    @commands.Cog.listener()
    async def on_message_delete(self, message: nextcord.Message):
        if not message.guild:
            return

        config = self.get_guild_config(message.guild.id)
        if config["enabled"] and config["log_types"].get("message_delete", False):
            log_channel = self.get_log_channel(message.guild, config)
            if log_channel:
                embed = Embed(
                    title="🗑️ Message Deleted",
                    description=f"**Author:** {message.author.mention}\n**Content:** {message.content}",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Message ID: {message.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: nextcord.Message, after: nextcord.Message):
        if not before.guild:
            return

        config = self.get_guild_config(before.guild.id)
        if config["enabled"] and config["log_types"].get("message_edit", False):
            log_channel = self.get_log_channel(before.guild, config)
            if log_channel and before.content != after.content:
                embed = Embed(
                    title="✏️ Message Edited",
                    description=(
                        f"**Author:** {before.author.mention}\n"
                        f"**Before:** {before.content}\n"
                        f"**After:** {after.content}"
                    ),
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Message ID: {before.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        config = self.get_guild_config(member.guild.id)
        if config["enabled"] and config["log_types"].get("member_join", False):
            log_channel = self.get_log_channel(member.guild, config)
            if log_channel:
                embed = Embed(
                    title="✅ Member Joined",
                    description=f"{member.mention} has joined the server.",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {member.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        config = self.get_guild_config(member.guild.id)
        if config["enabled"] and config["log_types"].get("member_leave", False):
            log_channel = self.get_log_channel(member.guild, config)
            if log_channel:
                embed = Embed(
                    title="❌ Member Left",
                    description=f"{member.mention} has left the server.",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {member.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: nextcord.Guild, user: nextcord.User):
        config = self.get_guild_config(guild.id)
        if config["enabled"] and config["log_types"].get("member_ban", False):
            log_channel = self.get_log_channel(guild, config)
            if log_channel:
                embed = Embed(
                    title="🔨 Member Banned",
                    description=f"{user.mention} has been banned from the server.",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {user.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: nextcord.Guild, user: nextcord.User):
        config = self.get_guild_config(guild.id)
        if config["enabled"] and config["log_types"].get("member_unban", False):
            log_channel = self.get_log_channel(guild, config)
            if log_channel:
                embed = Embed(
                    title="🔓 Member Unbanned",
                    description=f"{user.mention} has been unbanned from the server.",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {user.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: nextcord.Role, after: nextcord.Role):
        config = self.get_guild_config(before.guild.id)
        if config["enabled"] and config["log_types"].get("role_update", False):
            log_channel = self.get_log_channel(before.guild, config)
            if log_channel and (before.name != after.name or before.permissions != after.permissions):
                embed = Embed(
                    title="🛠️ Role Updated",
                    description=(
                        f"**Role:** {after.mention}\n"
                        f"**Before:** {before.name} - {before.permissions}\n"
                        f"**After:** {after.name} - {after.permissions}"
                    ),
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Role ID: {after.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: nextcord.abc.GuildChannel):
        config = self.get_guild_config(channel.guild.id)
        if config["enabled"] and config["log_types"].get("channel_create", False):
            log_channel = self.get_log_channel(channel.guild, config)
            if log_channel:
                embed = Embed(
                    title="📝 Channel Created",
                    description=(
                        f"**Name:** {channel.name}\n"
                        f"**Type:** {channel.type}\n"
                        f"**Category:** {channel.category.name if channel.category else 'None'}"
                    ),
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Channel ID: {channel.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: nextcord.abc.GuildChannel):
        config = self.get_guild_config(channel.guild.id)
        if config["enabled"] and config["log_types"].get("channel_delete", False):
            log_channel = self.get_log_channel(channel.guild, config)
            if log_channel:
                embed = Embed(
                    title="🗑️ Channel Deleted",
                    description=(
                        f"**Name:** {channel.name}\n"
                        f"**Type:** {channel.type}\n"
                        f"**Category:** {channel.category.name if channel.category else 'None'}"
                    ),
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Channel ID: {channel.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: nextcord.abc.GuildChannel, after: nextcord.abc.GuildChannel):
        config = self.get_guild_config(before.guild.id)
        if config["enabled"] and config["log_types"].get("channel_update", False):
            log_channel = self.get_log_channel(before.guild, config)
            if log_channel:
                changes = []
                if before.name != after.name:
                    changes.append(f"**Name:** {before.name} → {after.name}")
                if before.category != after.category:
                    changes.append(f"**Category:** {before.category.name if before.category else 'None'} → {after.category.name if after.category else 'None'}")
                if before.position != after.position:
                    changes.append(f"**Position:** {before.position} → {after.position}")
                
                if changes:
                    embed = Embed(
                        title="🔄 Channel Updated",
                        description="\n".join(changes),
                        color=0xffff00,
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text=f"Channel ID: {after.id}")
                    await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
        config = self.get_guild_config(member.guild.id)
        if config["enabled"] and config["log_types"].get("voice_state", False):
            log_channel = self.get_log_channel(member.guild, config)
            if log_channel:
                if not before.channel and after.channel:
                    action = f"joined {after.channel.mention}"
                elif before.channel and not after.channel:
                    action = f"left {before.channel.mention}"
                elif before.channel != after.channel:
                    action = f"moved from {before.channel.mention} to {after.channel.mention}"
                else:
                    return

                embed = Embed(
                    title="🎤 Voice State Update",
                    description=f"{member.mention} {action}",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {member.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: nextcord.Role):
        config = self.get_guild_config(role.guild.id)
        if config["enabled"] and config["log_types"].get("role_create", False):
            log_channel = self.get_log_channel(role.guild, config)
            if log_channel:
                embed = Embed(
                    title="➕ Role Created",
                    description=(
                        f"**Name:** {role.name}\n"
                        f"**Color:** {role.color}\n"
                        f"**Hoisted:** {role.hoist}\n"
                        f"**Mentionable:** {role.mentionable}"
                    ),
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Role ID: {role.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: nextcord.Role):
        config = self.get_guild_config(role.guild.id)
        if config["enabled"] and config["log_types"].get("role_delete", False):
            log_channel = self.get_log_channel(role.guild, config)
            if log_channel:
                embed = Embed(
                    title="➖ Role Deleted",
                    description=f"**Name:** {role.name}",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Role ID: {role.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: nextcord.Member, after: nextcord.Member):
        config = self.get_guild_config(before.guild.id)
        if config["enabled"] and config["log_types"].get("member_timeout", False):
            log_channel = self.get_log_channel(before.guild, config)
            if log_channel and before.communication_disabled_until != after.communication_disabled_until:
                if after.communication_disabled_until:
                    action = f"timed out until {after.communication_disabled_until.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                else:
                    action = "timeout removed"

                embed = Embed(
                    title="⏰ Member Timeout",
                    description=f"{after.mention} has been {action}",
                    color=0xffff00,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"User ID: {after.id}")
                await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(LoggingListener(bot))