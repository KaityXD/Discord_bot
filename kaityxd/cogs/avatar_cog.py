import nextcord
from nextcord import IntegrationType, Interaction, InteractionContextType, Embed
from nextcord.ext import commands

class AvatarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        description="Show the avatar of a user or yourself.",
        integration_types=[
            IntegrationType.user_install,
            IntegrationType.guild_install,
        ],
        contexts=[
            InteractionContextType.guild,
            InteractionContextType.bot_dm,
            InteractionContextType.private_channel,
        ],
    )
    async def ava(self, interaction: Interaction, user: nextcord.User = None):
        target_user = user or interaction.user
        embed = Embed(title=f"{target_user.name}'s Avatar", color=nextcord.Color.blurple())
        embed.set_image(url=target_user.avatar.url)
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(AvatarCog(bot))
    