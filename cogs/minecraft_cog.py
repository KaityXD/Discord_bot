import nextcord
from nextcord import slash_command, Interaction
from nextcord.ext import commands
import httpx
import json
import asyncio

class MinecraftSkinViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @slash_command(
        name="skin3d",
        description="View a 3D render of a Minecraft player's skin"
    )
    async def skin3d(
        self, 
        interaction: Interaction,
        username: str = nextcord.SlashOption(
            name="username",
            description="Minecraft username to get the skin for",
            required=True
        )
    ):
        await interaction.response.defer()
        
        try:
            embed = nextcord.Embed(
                title=f"3D Skin Viewer - {username}",
                color=nextcord.Color.green()
            )
            
            front_url = f"https://mc-heads.net/body/{username}"
            head_url = f"https://mc-heads.net/head/{username}"
            
            embed.set_image(url=front_url)
            embed.set_thumbnail(url=head_url)
            
            class SkinViewButtons(nextcord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    
                @nextcord.ui.button(label="Front", style=nextcord.ButtonStyle.primary)
                async def front_view(self, button: nextcord.ui.Button, interaction: Interaction):
                    embed.set_image(url=f"https://mc-heads.net/body/{username}/front")
                    await interaction.response.edit_message(embed=embed)
                    
                @nextcord.ui.button(label="Back", style=nextcord.ButtonStyle.primary)
                async def back_view(self, button: nextcord.ui.Button, interaction: Interaction):
                    embed.set_image(url=f"https://mc-heads.net/body/{username}/back")
                    await interaction.response.edit_message(embed=embed)
                    
                @nextcord.ui.button(label="Left", style=nextcord.ButtonStyle.primary)
                async def left_view(self, button: nextcord.ui.Button, interaction: Interaction):
                    embed.set_image(url=f"https://mc-heads.net/body/{username}/left")
                    await interaction.response.edit_message(embed=embed)
                    
                @nextcord.ui.button(label="Right", style=nextcord.ButtonStyle.primary)
                async def right_view(self, button: nextcord.ui.Button, interaction: Interaction):
                    embed.set_image(url=f"https://mc-heads.net/body/{username}/right")
                    await interaction.response.edit_message(embed=embed)

            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
                if resp.status_code != 200:
                    await interaction.followup.send(f"❌ Could not find player: {username}")
                    return
            
            await interaction.followup.send(embed=embed, view=SkinViewButtons())
            
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

def setup(bot):
    bot.add_cog(MinecraftSkinViewer(bot))
  
