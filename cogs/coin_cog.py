import random
import nextcord
from nextcord.ext import commands
from nextcord import Interaction

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="flip", description="Flip a coin and get heads or tails.")
    async def flip(self, interaction: Interaction):
        outcome = random.choice(["Heads", "Tails"])
        embed = nextcord.Embed(
            title="🪙 Coin Flip Result",
            description=f"{interaction.user.mention} got {outcome}!",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(CoinFlip(bot))
    