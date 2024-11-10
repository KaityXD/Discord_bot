import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SelectOption
from nextcord import slash_command
from utils.music_utils import create_embed



class Utils_cogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="[🔍] Checking Ping")
    async def ping(self, interaction: nextcord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.send(f"Pong!: {latency}ms")

    @nextcord.slash_command(name="avatar", description="[👩] Get user profile")
    async def avatar(self, interaction: nextcord.Interaction, member: nextcord.Member):
        await interaction.response.defer()
        await interaction.followup.send(f"[Profile]({member.avatar.url}) of {member.mention}")

    @nextcord.slash_command(name="invite", description="[📎] Get invite link!")
    async def invite(self, interaction: nextcord.Interaction):
        embed = create_embed("📎 Invitelink", "[KaityXD](https://discord.com/oauth2/authorize?client_id=1205730493891485706) :D")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.set_footer(text="Thankyou for support ❤️")
        await interaction.send(embed=embed)



def setup(bot):
    bot.add_cog(Utils_cogs(bot))
