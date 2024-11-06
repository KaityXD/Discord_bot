import nextcord
from nextcord import IntegrationType, Interaction, InteractionContextType
from nextcord.ext import commands
import httpx

class FunFactsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="funfact", 
        description="Get a random fun fact from the web!",
        integration_types=[
        IntegrationType.user_install, 
        IntegrationType.guild_install,
    ],
    contexts=[
        InteractionContextType.guild,  
        InteractionContextType.bot_dm,  
        InteractionContextType.private_channel,  
    ],)
    async def funfact(self, ctx):
        async with httpx.AsyncClient() as client:
            response = await client.get("https://uselessfacts.jsph.pl/random.json?language=en")
            if response.status_code == 200:
                data = response.json()
                fact = data.get("text", "Could not fetch a fun fact at the moment.")
            else:
                fact = "Oops! I couldn't retrieve a fun fact right now. Try again later."

   
        embed = nextcord.Embed(title="🎉 Fun Fact", description=fact, color=0x00ff00)
        embed.set_footer(text="Isn't that cool?")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(FunFactsCog(bot))
