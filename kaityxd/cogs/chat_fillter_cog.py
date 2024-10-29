import nextcord
from nextcord.ext import commands
import sqlite3
from typing import Dict, List

class Filter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_path = "database/chat_filter.db"
        self.cache: Dict[int, Dict[str, List[str]]] = {}
        self.setup_database()
        bot.add_listener(self.on_message)

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS filters (
                    guild_id INTEGER PRIMARY KEY,
                    words TEXT DEFAULT '[]',
                    whitelist TEXT DEFAULT '[]'
                )
                """
            )
            conn.commit()

    def load_filter(self, guild_id: int) -> Dict[str, List[str]]:
        if guild_id in self.cache:
            return self.cache[guild_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT words, whitelist FROM filters WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()

            if result:
                words = eval(result[0])
                whitelist = eval(result[1])
            else:
                words, whitelist = [], []
                cursor.execute("INSERT INTO filters (guild_id, words, whitelist) VALUES (?, '[]', '[]')", (guild_id,))
                conn.commit()

            data = {"words": words, "whitelist": whitelist}
            self.cache[guild_id] = data
            return data

    def save_filter(self, guild_id: int, data: Dict[str, List[str]]) -> None:
        self.cache[guild_id] = data
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE filters SET words = ?, whitelist = ? WHERE guild_id = ?",
                (str(data["words"]), str(data["whitelist"]), guild_id)
            )
            conn.commit()

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
        if len(word) < 2:
            await interaction.response.send_message(embed=self.create_embed("Error", "Word must be at least 2 characters long.", 0xFF0000), ephemeral=True)
            return

        guild_id = interaction.guild_id
        data = self.load_filter(guild_id)

        word = word.strip()
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

        word = word_or_id.strip()
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
            except nextcord.Forbidden:
                pass
            except nextcord.HTTPException:
                pass

def setup(bot: commands.Bot):
    bot.add_cog(Filter(bot))
