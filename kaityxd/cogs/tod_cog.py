import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import random
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    DATABASE_DIR: Path = Path("database/truth_or_dare")
    TRUTH_OR_DARE_FILE: Path = DATABASE_DIR / "truth_or_dare.json"
    WHITELIST_FILE: Path = DATABASE_DIR / "whitelist.json"
    BUTTON_TIMEOUT: int = 120

class DatabaseManager:
    def __init__(self, config: Config):
        self.config = config
        self._ensure_directories()
        self.data = self._load_data()
        self.whitelist = self._load_whitelist()

    def _ensure_directories(self) -> None:
        self.config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict[str, List[str]]:
        try:
            if self.config.TRUTH_OR_DARE_FILE.exists():
                with open(self.config.TRUTH_OR_DARE_FILE, "r") as f:
                    return json.load(f)
            return {"truths": [], "dares": []}
        except json.JSONDecodeError:
            print(f"Error reading {self.config.TRUTH_OR_DARE_FILE}. Creating new data file.")
            return {"truths": [], "dares": []}

    def _load_whitelist(self) -> List[int]:
        try:
            if self.config.WHITELIST_FILE.exists():
                with open(self.config.WHITELIST_FILE, "r") as f:
                    return json.load(f)
            return []
        except json.JSONDecodeError:
            print(f"Error reading {self.config.WHITELIST_FILE}. Creating new whitelist.")
            return []

    def save_data(self) -> None:
        try:
            with open(self.config.TRUTH_OR_DARE_FILE, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def save_whitelist(self) -> None:
        try:
            with open(self.config.WHITELIST_FILE, "w") as f:
                json.dump(self.whitelist, f, indent=4)
        except Exception as e:
            print(f"Error saving whitelist: {e}")

class TruthOrDareView(nextcord.ui.View):
    def __init__(self, user: nextcord.Member, truths: List[str], dares: List[str]):
        super().__init__(timeout=Config.BUTTON_TIMEOUT)
        self.user = user
        self.truths = truths
        self.dares = dares

    async def _handle_choice(self, interaction: Interaction, choice_type: str, choices: List[str]) -> None:
        if interaction.user != self.user:
            await interaction.response.send_message("You cannot select in this game.", ephemeral=True)
            return

        if not choices:
            await interaction.response.send_message(f"No {choice_type}s available!", ephemeral=True)
            self.stop()
            return

        choice = random.choice(choices)
        embed = nextcord.Embed(
            title=f"🎲 Truth or Dare - {choice_type.capitalize()}",
            description=choice,
            color=nextcord.Color.blue() if choice_type == "truth" else nextcord.Color.red()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        self.stop()

    @nextcord.ui.button(label="Truth", style=nextcord.ButtonStyle.primary, emoji="🤔")
    async def truth_button(self, button: nextcord.ui.Button, interaction: Interaction):
        await self._handle_choice(interaction, "truth", self.truths)

    @nextcord.ui.button(label="Dare", style=nextcord.ButtonStyle.danger, emoji="🎯")
    async def dare_button(self, button: nextcord.ui.Button, interaction: Interaction):
        await self._handle_choice(interaction, "dare", self.dares)

class TruthOrDareCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseManager(Config())

    def _check_whitelist(self, user_id: int) -> bool:
        return user_id in self.db.whitelist

    def _create_game_embed(self, user: nextcord.Member, target: Optional[nextcord.Member] = None) -> nextcord.Embed:
        embed = nextcord.Embed(
            title="🎲 Truth or Dare",
            description="Choose your fate: Truth or Dare?",
            color=nextcord.Color.gold()
        )
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        if target:
            embed.add_field(name="Player", value=target.mention, inline=True)
            embed.add_field(name="Challenged by", value=user.mention, inline=True)
        else:
            embed.add_field(name="Player", value=user.mention, inline=True)
        return embed

    @nextcord.slash_command(name="truth_or_dare", description="[❓] Play a game of Truth or Dare")
    async def truth_or_dare(self, interaction: Interaction):
        pass

    @truth_or_dare.subcommand(name="play", description="[❓] Play a game of Truth or Dare")
    async def play(self, interaction: Interaction):
        embed = self._create_game_embed(interaction.user)
        view = TruthOrDareView(interaction.user, self.db.data["truths"], self.db.data["dares"])
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()

    @truth_or_dare.subcommand(name="send_to", description="[❓] Send Truth or Dare to a selected user")
    async def send_to(
        self,
        interaction: Interaction,
        member: nextcord.Member = SlashOption(name="user", description="Select the user")
    ):
        if member.bot:
            await interaction.response.send_message("You cannot send Truth or Dare to a bot!", ephemeral=True)
            return

        embed = self._create_game_embed(interaction.user, member)
        view = TruthOrDareView(member, self.db.data["truths"], self.db.data["dares"])
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()

    @truth_or_dare.subcommand(name="add", description="[💯] Add a new Truth or Dare")
    async def add(
        self,
        interaction: Interaction,
        category: str = SlashOption(
            name="category",
            choices={"truth": "truth", "dare": "dare"},
            description="Select category"
        ),
        message: str = SlashOption(name="message", description="[🗨️] Message to add")
    ):
        if not self._check_whitelist(interaction.user.id):
            embed = nextcord.Embed(
                title="❌ Access Denied",
                description="You are not allowed to add Truth or Dare prompts.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        category_list = f"{category}s"
        if message in self.db.data[category_list]:
            embed = nextcord.Embed(
                title="❌ Duplicate Entry",
                description=f"This {category} already exists!",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.db.data[category_list].append(message)
        self.db.save_data()
        embed = nextcord.Embed(
            title="✅ Added Successfully",
            description=f"Added new {category}:\n{message}",
            color=nextcord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @truth_or_dare.subcommand(name="delete", description="[❓] Delete a Truth or Dare")
    async def delete(
        self,
        interaction: Interaction,
        category: str = SlashOption(
            name="category",
            choices={"truth": "truth", "dare": "dare"},
            description="Select category"
        ),
        message: str = SlashOption(name="message", description="[❓] Message to delete")
    ):
        if not self._check_whitelist(interaction.user.id):
            embed = nextcord.Embed(
                title="❌ Access Denied",
                description="You are not allowed to delete Truth or Dare prompts.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        category_list = f"{category}s"
        if message in self.db.data[category_list]:
            self.db.data[category_list].remove(message)
            self.db.save_data()
            embed = nextcord.Embed(
                title="✅ Deleted Successfully",
                description=f"Removed {category}:\n{message}",
                color=nextcord.Color.green()
            )
        else:
            embed = nextcord.Embed(
                title="❌ Not Found",
                description=f"'{message}' not found in {category} list.",
                color=nextcord.Color.red()
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @truth_or_dare.subcommand(name="whitelist", description="[📜] Manage the whitelist for adding Truth or Dare")
    async def whitelist(
        self,
        interaction: Interaction,
        action: str = SlashOption(
            name="action",
            choices={"add": "add", "remove": "remove"},
            description="[📜] Add or remove a user from the whitelist"
        ),
        user: nextcord.User = SlashOption(name="user", description="[📜] User to add/remove")
    ):
        if not self._check_whitelist(interaction.user.id):
            embed = nextcord.Embed(
                title="❌ Access Denied",
                description="You are not allowed to manage the whitelist.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if action == "add":
            if user.id not in self.db.whitelist:
                self.db.whitelist.append(user.id)
                self.db.save_whitelist()
                embed = nextcord.Embed(
                    title="✅ Whitelist Updated",
                    description=f"{user.mention} has been added to the whitelist.",
                    color=nextcord.Color.green()
                )
            else:
                embed = nextcord.Embed(
                    title="ℹ️ Already Whitelisted",
                    description=f"{user.mention} is already whitelisted.",
                    color=nextcord.Color.blue()
                )
        else:
            if user.id in self.db.whitelist:
                self.db.whitelist.remove(user.id)
                self.db.save_whitelist()
                embed = nextcord.Embed(
                    title="✅ Whitelist Updated",
                    description=f"{user.mention} has been removed from the whitelist.",
                    color=nextcord.Color.green()
                )
            else:
                embed = nextcord.Embed(
                    title="ℹ️ Not Found",
                    description=f"{user.mention} is not in the whitelist.",
                    color=nextcord.Color.blue()
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TruthOrDareCog(bot))