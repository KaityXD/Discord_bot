import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import json
import os
from typing import Dict, Any

class Tag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_prefix = '?'

    def load_guild_data(self, guild_id: int) -> Dict[str, Any]:
        file_path = f'database/guilds/{guild_id}_data.json'
        default_data = {"prefix": self.default_prefix, "tags": {}, "allowed_roles": []}
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            pass
        return default_data

    def save_guild_data(self, guild_id: int, data: Dict[str, Any]) -> None:
        os.makedirs('database/guilds', exist_ok=True)
        file_path = f'database/guilds/{guild_id}_data.json'
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    async def can_manage_tags(self, interaction: Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        guild_data = self.load_guild_data(interaction.guild_id)
        return any(role.id in guild_data.get("allowed_roles", []) for role in interaction.user.roles)

    @nextcord.slash_command(name="tag", description="[📑] Manage server tags and custom commands")
    async def tag(self, interaction: Interaction):
        pass

    @tag.subcommand(name="roles", description="[👥] Manage roles that can create and edit tags")
    @commands.has_permissions(administrator=True)
    async def set_allowed_roles(self, interaction: Interaction,
        action: str = SlashOption(description="[⚙️] Add, remove, or list roles", choices=["add", "remove", "list"]),
        role: nextcord.Role = SlashOption(required=False, description="🎭 Role to manage")):
        guild_data = self.load_guild_data(interaction.guild_id)
        if action == "list":
            allowed_roles = guild_data.get("allowed_roles", [])
            if not allowed_roles:
                await interaction.response.send_message("📝 No roles are currently allowed to manage tags.", ephemeral=True)
                return
            role_mentions = [f"<@&{role_id}>" for role_id in allowed_roles if interaction.guild.get_role(role_id)]
            await interaction.response.send_message(f"👥 Roles that can manage tags:\n{', '.join(role_mentions)}", ephemeral=True)
            return
        if not role:
            await interaction.response.send_message("❗ Please specify a role!", ephemeral=True)
            return
        if "allowed_roles" not in guild_data:
            guild_data["allowed_roles"] = []
        if action == "add":
            if role.id not in guild_data["allowed_roles"]:
                guild_data["allowed_roles"].append(role.id)
                await interaction.response.send_message(f"✅ Added {role.mention} to tag managers", ephemeral=True)
            else:
                await interaction.response.send_message(f"ℹ️ {role.mention} is already a tag manager", ephemeral=True)
        else:
            if role.id in guild_data["allowed_roles"]:
                guild_data["allowed_roles"].remove(role.id)
                await interaction.response.send_message(f"🗑️ Removed {role.mention} from tag managers", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {role.mention} is not a tag manager", ephemeral=True)
        self.save_guild_data(interaction.guild_id, guild_data)

    @tag.subcommand(name="prefix", description="[⚡ ]Set the prefix for tag commands")
    async def set_prefix(self, interaction: Interaction,
        new_prefix: str = SlashOption(description="[💫] New prefix for tags")):
        if not await self.can_manage_tags(interaction):
            await interaction.response.send_message("❌ You don't have permission to manage tags!", ephemeral=True)
            return
        guild_data = self.load_guild_data(interaction.guild_id)
        guild_data["prefix"] = new_prefix
        self.save_guild_data(interaction.guild_id, guild_data)
        await interaction.response.send_message(f"✅ Tag prefix has been set to `{new_prefix}`", ephemeral=True)

    @tag.subcommand(name="list", description="[📋] Show all available tags")
    async def list_tags(self, interaction: Interaction):
        await interaction.response.defer()
        guild_data = self.load_guild_data(interaction.guild_id)
        tags = guild_data.get("tags", {})
        if not tags:
            await interaction.followup.send("📝 No tags found in this server", ephemeral=True)
            return
        sorted_tags = sorted(tags.items(), key=lambda x: x[1]['id'])
        embed = Embed(title="📑 All Tags", color=0x3498db)
        embed.set_footer(text=f"Prefix: {guild_data.get('prefix', self.default_prefix)}")
        for tag_name, tag_data in sorted_tags:
            creator = interaction.guild.get_member(tag_data['created_by'])
            creator_name = creator.name if creator else "Unknown"
            embed.add_field(name=f"🏷️ ID: {tag_data['id']} | {tag_name}",
                          value=f"```{tag_data['message'][:100]}{'...' if len(tag_data['message']) > 100 else ''}```\n👤 Created by: {creator_name}",
                          inline=False)
        await interaction.followup.send(embed=embed)

    @tag.subcommand(name="add", description="✨ Create a new tag")
    async def add_tag(self, interaction: Interaction,
        tag_name: str = SlashOption(description="[📝] Name of the tag to create")):
        if not await self.can_manage_tags(interaction):
            await interaction.response.send_message("❌ You don't have permission to manage tags!", ephemeral=True)
            return
        guild_data = self.load_guild_data(interaction.guild_id)
        if tag_name in guild_data.get("tags", {}):
            await interaction.response.send_message(f"❌ Tag `{tag_name}` already exists!", ephemeral=True)
            return
        await interaction.response.send_modal(self.TagModal(self, interaction.guild_id, tag_name))

    class TagModal(nextcord.ui.Modal):
        def __init__(self, cog, guild_id, tag_name):
            self.cog = cog
            self.guild_id = guild_id
            self.tag_name = tag_name
            super().__init__(title="✨ Add Tag")
            self.tag_content = nextcord.ui.TextInput(
                label="📝 Tag Content",
                placeholder="Enter the content for your tag",
                style=nextcord.TextInputStyle.paragraph,
                required=True,
                min_length=1,
                max_length=2000
            )
            self.add_item(self.tag_content)

        async def callback(self, interaction: Interaction):
            tag_message = self.tag_content.value
            guild_data = self.cog.load_guild_data(self.guild_id)
            if "tags" not in guild_data:
                guild_data["tags"] = {}
            used_ids = {tag_data['id'] for tag_data in guild_data["tags"].values()}
            tag_id = 1
            while tag_id in used_ids:
                tag_id += 1
            guild_data["tags"][self.tag_name] = {
                "id": tag_id,
                "message": tag_message,
                "created_by": interaction.user.id,
                "created_at": str(interaction.created_at)
            }
            self.cog.save_guild_data(self.guild_id, guild_data)
            embed = Embed(title="✨ Tag Added", color=0x2ecc71)
            embed.add_field(name="📝 Name", value=self.tag_name, inline=False)
            embed.add_field(name="ID", value=str(tag_id), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @tag.subcommand(name="delete", description="[🗑️] Delete an existing tag")
    async def delete_tag(self, interaction: Interaction,
        identifier: str = SlashOption(description="[🔍] Tag name or ID to delete")):
        if not await self.can_manage_tags(interaction):
            await interaction.response.send_message("❌ You don't have permission to manage tags!", ephemeral=True)
            return
        guild_data = self.load_guild_data(interaction.guild_id)
        tags = guild_data.get("tags", {})
        if identifier in tags:
            del tags[identifier]
            guild_data["tags"] = tags
            self.save_guild_data(interaction.guild_id, guild_data)
            await interaction.response.send_message(f"✅ Deleted tag `{identifier}`", ephemeral=True)
            return
        try:
            tag_id = int(identifier)
            for tag_name, tag_data in tags.items():
                if tag_data['id'] == tag_id:
                    del tags[tag_name]
                    guild_data["tags"] = tags
                    self.save_guild_data(interaction.guild_id, guild_data)
                    await interaction.response.send_message(f"✅ Deleted tag `{tag_name}` (ID: {tag_id})", ephemeral=True)
                    return
        except ValueError:
            pass
        await interaction.response.send_message(f"❌ No tag found matching `{identifier}`", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        guild_data = self.load_guild_data(message.guild.id)
        prefix = guild_data.get("prefix", self.default_prefix)
        if not message.content.startswith(prefix):
            return
        tag_name = message.content[len(prefix):].strip()
        tags = guild_data.get("tags", {})

        response_message = None
        if tag_name in tags:
            response_message = tags[tag_name]["message"]
        else:
            try:
                tag_id = int(tag_name)
                for tag_data in tags.values():
                    if tag_data['id'] == tag_id:
                        response_message = tag_data["message"]
                        break
            except ValueError:
                return

        if response_message:
            if message.reference and message.reference.message_id:
                referenced_message = await message.channel.fetch_message(message.reference.message_id)
                await referenced_message.reply(response_message)
            else:
                await message.channel.send(response_message)

def setup(bot):
    bot.add_cog(Tag(bot))