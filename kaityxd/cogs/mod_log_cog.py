import json
import nextcord
from nextcord.ext import commands
from nextcord import Embed
import os
from datetime import datetime
from typing import Literal

class ModLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_path = "database/mod_logs"
        self.ensure_directory()
        
    def ensure_directory(self):
        """Ensure the database directory exists"""
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def get_config_path(self, guild_id: int) -> str:
        """Get the path for a guild's config file"""
        return os.path.join(self.base_path, f"{guild_id}.json")

    def load_config(self, guild_id: int) -> dict:
        """Load config for a specific guild"""
        config_path = self.get_config_path(guild_id)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.get_default_config()

    def save_config(self, guild_id: int, config: dict):
        """Save config for a specific guild"""
        config_path = self.get_config_path(guild_id)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_default_config(self) -> dict:
        """Get default configuration for a new guild"""
        return {
            "enabled": False,
            "log_channel": None,
            "log_types": {
                "message_delete": True,
                "message_edit": True,
                "member_ban": True,
                "member_unban": True,
                "role_update": True,
                "member_join": True,
                "member_leave": True,
                "nickname_change": True,
                "channel_create": True,
                "channel_delete": True,
                "channel_update": True,
                "voice_state": True,
                "role_create": True,
                "role_delete": True,
                "member_timeout": True
            }
        }

    def get_guild_config(self, guild_id: int) -> dict:
        """Get configuration for a specific guild"""
        config = self.load_config(guild_id)
        # Ensure all default config keys exist
        default_config = self.get_default_config()
        modified = False
        
        # Add any missing keys from default config
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
                modified = True
            elif key == "log_types":
                for type_key, type_value in default_config["log_types"].items():
                    if type_key not in config["log_types"]:
                        config["log_types"][type_key] = type_value
                        modified = True

        if modified:
            self.save_config(guild_id, config)
            
        return config

    # [Previous event listeners remain the same...]

    @nextcord.slash_command(name="mod_log", description="Manage server moderation logging settings")
    async def mod_log(self, interaction: nextcord.Interaction):
        pass

    @mod_log.subcommand(name="set_channel", description="Set the channel for logging events")
    async def set_channel(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
            return

        config = self.get_guild_config(interaction.guild.id)
        config["log_channel"] = channel.id
        self.save_config(interaction.guild.id, config)

        embed = Embed(
            title="✅ Channel Set Successfully",
            description=f"Logging channel has been set to {channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod_log.subcommand(name="toggle", description="Enable or disable all logging")
    async def toggle_logging(self, interaction: nextcord.Interaction, 
                           action: Literal['enable', 'disable']):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
            return

        config = self.get_guild_config(interaction.guild.id)
        config["enabled"] = action == 'enable'
        self.save_config(interaction.guild.id, config)

        status = "enabled" if action == 'enable' else "disabled"
        embed = Embed(
            title=f"✅ Logging {status.capitalize()}",
            description=f"All logging has been {status}",
            color=0x00ff00 if action == 'enable' else 0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod_log.subcommand(name="type", description="Enable or disable specific logging types")
    async def toggle_type(self, interaction: nextcord.Interaction,
                         action: Literal['enable', 'disable'],
                         type: str):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
            return

        config = self.get_guild_config(interaction.guild.id)
        
        if type not in config["log_types"]:
            # Create a more readable format for available types
            available_types = "\n".join([
                f"• `{t.replace('_', ' ').title()}`" 
                for t in config["log_types"].keys()
            ])
            embed = Embed(
                title="❌ Invalid Type",
                description=f"Invalid log type specified. Available types:\n{available_types}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        config["log_types"][type] = action == 'enable'
        self.save_config(interaction.guild.id, config)

        status = "enabled" if action == 'enable' else "disabled"
        type_display = type.replace('_', ' ').title()
        embed = Embed(
            title=f"✅ Type {status.capitalize()}",
            description=f"`{type_display}` logging has been {status}",
            color=0x00ff00 if action == 'enable' else 0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod_log.subcommand(name="status", description="Show current logging configuration")
    async def show_status(self, interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You don't have permission to use this command", ephemeral=True)
            return

        config = self.get_guild_config(interaction.guild.id)
        
        # Create sections for enabled and disabled types
        enabled_types = []
        disabled_types = []
        for type_name, enabled in config["log_types"].items():
            display_name = type_name.replace('_', ' ').title()
            if enabled:
                enabled_types.append(f"✅ {display_name}")
            else:
                disabled_types.append(f"❌ {display_name}")

        channel_status = f"<#{config['log_channel']}>" if config['log_channel'] else "Not Set"
        
        embed = Embed(
            title="📊 Logging Status",
            description=(
                f"**Status:** {'✅ Enabled' if config['enabled'] else '❌ Disabled'}\n"
                f"**Channel:** {channel_status}\n\n"
                "**Enabled Types:**\n" + 
                ("\n".join(enabled_types) if enabled_types else "- None -") +
                "\n\n**Disabled Types:**\n" +
                ("\n".join(disabled_types) if disabled_types else "- None -")
            ),
            color=0x00ff00 if config['enabled'] else 0xff0000
        )
        
        # Add a footer with command help
        embed.set_footer(text="Use /mod_log type enable/disable <type> to manage individual types")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod_log.subcommand(name="help", description="Show help for mod_log commands")
    async def show_help(self, interaction: nextcord.Interaction):
        embed = Embed(
            title="📖 Mod Log Commands Help",
            description="Complete guide for moderation logging commands",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📝 Basic Commands",
            value=(
                "`/mod_log set_channel #channel` - Set logging channel\n"
                "`/mod_log toggle enable/disable` - Enable/disable all logging\n"
                "`/mod_log status` - Show current configuration\n"
                "`/mod_log help` - Show this help message"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Type Management",
            value=(
                "`/mod_log type enable <type>` - Enable specific log type\n"
                "`/mod_log type disable <type>` - Disable specific log type"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Available Log Types",
            value="\n".join([
                f"• `{type_name.replace('_', ' ').title()}`" 
                for type_name in self.get_default_config()["log_types"].keys()
            ]),
            inline=False
        )
        
        embed.set_footer(text="All commands require 'Manage Server' permission")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(ModLogging(bot))