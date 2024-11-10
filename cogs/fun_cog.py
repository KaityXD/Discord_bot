import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from PIL import Image
import httpx
from io import BytesIO

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(
        name="bonk",
        description="[🏏] Bonk someone!",
    )
    async def bonk(self, interaction: Interaction, user: nextcord.User):
        await interaction.response.defer()

        if not user.avatar:
            await interaction.followup.send("The user does not have an avatar.")
            return

        try:
            async with httpx.AsyncClient() as client:
                bonked_avatar_response = await client.get(user.avatar.url)
            bonked_avatar = Image.open(BytesIO(bonked_avatar_response.content)).convert("RGBA")
        except Exception as e:
            await interaction.followup.send(f"Failed to retrieve the avatar: {e}")
            return

        try:
            template = Image.open("images/bonk_template.png").convert("RGBA")
            avatar_size = 70
            bonked_avatar = bonked_avatar.resize((avatar_size, avatar_size))
            avatar_x = (template.width - avatar_size) // 2
            avatar_y = (template.height - avatar_size) // 2
            template.paste(bonked_avatar, (avatar_x, avatar_y), bonked_avatar)

            final_image = BytesIO()
            template.save(final_image, "PNG") 
            final_image.seek(0)
            await interaction.followup.send(
                content=f"{interaction.user.mention} bonked {user.mention}!",
                file=nextcord.File(final_image, "bonk.png")
            )
        except Exception as e:
            await interaction.followup.send(f"Failed to process the bonk image: {e}")

def setup(bot):
    bot.add_cog(Fun(bot))
