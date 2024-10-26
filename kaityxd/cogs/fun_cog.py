import nextcord
from nextcord import IntegrationType, Interaction, InteractionContextType
from nextcord.ext import commands
from PIL import Image
import requests
from io import BytesIO

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="bonk",
        description="[🏏] Bonk someone!",
        integration_types=[IntegrationType.user_install, IntegrationType.guild_install],
        contexts=[
            InteractionContextType.guild,
            InteractionContextType.bot_dm,
            InteractionContextType.private_channel,
        ],
    )
    async def bonk(self, interaction: Interaction, user_id: str):
        await interaction.response.defer()

        user = self.bot.get_user(user_id)

        if user is None:
            await interaction.followup.send("User not found.")
            return
        
        bonked_avatar_url = user.avatar.url if user.avatar else None
        
        if not bonked_avatar_url:
            await interaction.followup.send("The user does not have an avatar.")
            return

        try:
            bonked_avatar_response = requests.get(bonked_avatar_url)
            bonked_avatar = Image.open(BytesIO(bonked_avatar_response.content)).convert("RGBA")
        except Exception as e:
            await interaction.followup.send(f"Failed to retrieve the avatar: {e}")
            return

        template = Image.open("images/bonk_template.png").convert("RGBA")
        avatar_size = 70
        bonked_avatar = bonked_avatar.resize((avatar_size, avatar_size))
        avatar_x = (template.width - avatar_size) // 2
        avatar_y = (template.height - avatar_size) // 2
        template.paste(bonked_avatar, (avatar_x, avatar_y), bonked_avatar)

        final_image = BytesIO()
        template.save(final_image, "PNG") 
        final_image.seek(0)
        await interaction.followup.send(file=nextcord.File(final_image, "bonk.png"))

def setup(bot):
    bot.add_cog(Fun(bot))
