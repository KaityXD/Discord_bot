import nextcord
from nextcord.ext import commands
import json
import os
from typing import Dict, List, Optional

class Filter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.filter_dir = "database/chat_filter"
        self.cache: Dict[int, Dict[str, List[str]]] = {}
        bot.add_listener(self.on_message)

    def get_filter_path(self, guild_id: int) -> str:
        return os.path.join(self.filter_dir, f"{guild_id}_settings.json")

    def load_filter(self, guild_id: int) -> Dict[str, List[str]]:
        if guild_id in self.cache:
            return self.cache[guild_id]
        
        path = self.get_filter_path(guild_id)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if "whitelist" not in data:
                        data["whitelist"] = []
                    self.cache[guild_id] = data
                    return data
            except json.JSONDecodeError:
                return {"words": [], "whitelist": []}
        return {"words": [], "whitelist": []}

    def save_filter(self, guild_id: int, data: Dict[str, List[str]]) -> None:
        os.makedirs(self.filter_dir, exist_ok=True)
        path = self.get_filter_path(guild_id)
        self.cache[guild_id] = data
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def create_embed(self, title: str, description: str, color: int = 0x2b2d31) -> nextcord.Embed:
        embed = nextcord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Filter System")
        return embed

    @nextcord.slash_command(name="filter", description="Manage the chat filter system.")
    async def filter(self, interaction: nextcord.Interaction):
        pass

    @filter.subcommand(name="add", description="Add a word to the filter list.")
    @commands.has_permissions(manage_messages=True)
    async def add(self, interaction: nextcord.Interaction, word: str):
        if not word.isascii() or not word.replace(' ', '').isalnum():
            await interaction.response.send_message(embed=self.create_embed("Error", "Only English letters and numbers are allowed.", 0xFF0000), ephemeral=True)
            return

        if len(word) < 2:
            await interaction.response.send_message(embed=self.create_embed("Error", "Word must be at least 2 characters long.", 0xFF0000), ephemeral=True)
            return

        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)
        
        word = word.lower().strip()
        if word in data["words"]:
            await interaction.response.send_message(embed=self.create_embed("Error", f"The word '{word}' is already in the filter list.", 0xFF0000), ephemeral=True)
            return

        data["words"].append(word)
        self.save_filter(guild_id, data)
        await interaction.response.send_message(embed=self.create_embed("Success", f"Added '{word}' to the filter list.", 0x00FF00), ephemeral=True)

    @filter.subcommand(name="delete", description="Remove a word from the filter list.")
    @commands.has_permissions(manage_messages=True)
    async def delete(self, interaction: nextcord.Interaction, word_or_id: str):
        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)

        word = word_or_id.lower().strip()
        if word in data["words"]:
            data["words"].remove(word)
            self.save_filter(guild_id, data)
            await interaction.response.send_message(embed=self.create_embed("Success", f"Removed '{word}' from the filter list.", 0x00FF00), ephemeral=True)
            return

        try:
            index = int(word_or_id) - 1
            if 0 <= index < len(data["words"]):
                removed_word = data["words"].pop(index)
                self.save_filter(guild_id, data)
                await interaction.response.send_message(embed=self.create_embed("Success", f"Removed '{removed_word}' from the filter list.", 0x00FF00), ephemeral=True)
            else:
                await interaction.response.send_message(embed=self.create_embed("Error", "Invalid ID specified.", 0xFF0000), ephemeral=True)
        except ValueError:
            await interaction.response.send_message(embed=self.create_embed("Error", "Please provide a valid word or ID.", 0xFF0000), ephemeral=True)

    @filter.subcommand(name="list", description="Show the list of filtered words.")
    @commands.has_permissions(manage_messages=True)
    async def list(self, interaction: nextcord.Interaction):
        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)

        if not data["words"]:
            await interaction.response.send_message(embed=self.create_embed("Filter List", "No words in the filter list."), ephemeral=True)
            return

        chunks = []
        current_chunk = []
        for idx, word in enumerate(data["words"], 1):
            line = f"{idx}. {word}"
            current_chunk.append(line)
            
            if len("\n".join(current_chunk)) > 1800:
                chunks.append(current_chunk[:-1])
                current_chunk = [line]

        if current_chunk:
            chunks.append(current_chunk)

        for idx, chunk in enumerate(chunks):
            embed = self.create_embed(
                f"Filter List {f'(Continued {idx+1})' if idx > 0 else ''}",
                "\n".join(chunk)
            )
            if idx == 0:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

    @filter.subcommand(name="whitelist", description="Add a channel to the whitelist.")
    @commands.has_permissions(manage_messages=True)
    async def whitelist_add(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)
        
        if str(channel.id) in data["whitelist"]:
            await interaction.response.send_message(embed=self.create_embed("Error", f"{channel.mention} is already whitelisted.", 0xFF0000), ephemeral=True)
            return

        data["whitelist"].append(str(channel.id))
        self.save_filter(guild_id, data)
        await interaction.response.send_message(embed=self.create_embed("Success", f"Added {channel.mention} to the whitelist.", 0x00FF00), ephemeral=True)

    @filter.subcommand(name="unwhitelist", description="Remove a channel from the whitelist.")
    @commands.has_permissions(manage_messages=True)
    async def whitelist_remove(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)
        
        if str(channel.id) not in data["whitelist"]:
            await interaction.response.send_message(embed=self.create_embed("Error", f"{channel.mention} is not whitelisted.", 0xFF0000), ephemeral=True)
            return

        data["whitelist"].remove(str(channel.id))
        self.save_filter(guild_id, data)
        await interaction.response.send_message(embed=self.create_embed("Success", f"Removed {channel.mention} from the whitelist.", 0x00FF00), ephemeral=True)

    @filter.subcommand(name="whitelist_list", description="Show whitelisted channels.")
    @commands.has_permissions(manage_messages=True)
    async def whitelist_list(self, interaction: nextcord.Interaction):
        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)

        if not data["whitelist"]:
            await interaction.response.send_message(embed=self.create_embed("Whitelist", "No channels are whitelisted."), ephemeral=True)
            return

        channels = []
        for channel_id in data["whitelist"]:
            channel = interaction.guild.get_channel(int(channel_id))
            if channel:
                channels.append(f"• {channel.mention}")

        await interaction.response.send_message(
            embed=self.create_embed("Whitelisted Channels", "\n".join(channels) if channels else "No valid channels found."),
            ephemeral=True
        )

    async def on_message(self, message: nextcord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        data = self.load_filter(guild_id)
        
        if str(message.channel.id) in data["whitelist"]:
            return

        content = message.content.lower()
        if any(word in content for word in data["words"]):
            try:
                await message.delete()
                embed = self.create_embed("Message Deleted", f"{message.author.mention}, your message was deleted for containing filtered words.", 0xFF0000)
                await message.channel.send(embed=embed, delete_after=5)
            except nextcord.errors.Forbidden:
                pass

def setup(bot: commands.Bot):
    bot.add_cog(Filter(bot))