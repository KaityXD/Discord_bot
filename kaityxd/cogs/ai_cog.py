import json
import os
from typing import Dict, Any, List
import httpx
import nextcord
from nextcord.ext import commands
from utils.config import HEADERS
from utils.config import API_BASE_URL

class AICog(commands.Cog):
    """A cog for handling AI interactions using Cloudflare AI."""
    
    def __init__(self, bot):

        self.bot = bot
        self._setup_paths()
        self._load_data()
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30.0)

    def _setup_paths(self):
        """Set up file paths and create necessary directories."""
        self.base_dir = './database'
        self.guild_settings_file = f'{self.base_dir}/guild_settings.json'
        self.conversation_folder = f'{self.base_dir}/conversations'
        self.bot_identity_file = f'{self.base_dir}/bot_identity.json'
        
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.conversation_folder, exist_ok=True)

    def _load_data(self):
        """Load all necessary data files."""
        self.guild_settings = self._load_json_file(self.guild_settings_file, {})
        self.bot_identity = self._load_bot_identity()

    def _load_json_file(self, filepath: str, default: Dict) -> Dict:
        """Helper method to load JSON files with error handling."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading {filepath}: {e}")
        return default

    def _save_json_file(self, filepath: str, data: Dict) -> None:
        """Helper method to save JSON files with error handling."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")

    def _load_bot_identity(self) -> Dict[str, Any]:
        """Load or create default bot identity settings."""
        default_identity = {
            "name": self.bot.user.name if self.bot.user else "AI Assistant",
            "personality": "helpful and friendly",
            "background": "I am an AI assistant.",
            "interests": ["helping users", "learning new things"],
            "creator": "unknown",
            "creation_date": "unknown",
            "purpose": "to assist users"
        }
        
        identity = self._load_json_file(self.bot_identity_file, default_identity)
        if not os.path.exists(self.bot_identity_file):
            self._save_json_file(self.bot_identity_file, identity)
        return identity

    def get_identity_prompt(self) -> str:
        """Generate a prompt incorporating the bot's identity."""
        return f"""I am {self.bot_identity['name']}.
My personality is {self.bot_identity['personality']}.
Background: {self.bot_identity['background']}
Purpose: {self.bot_identity['purpose']}
Creator: {self.bot_identity['creator']}
Created: {self.bot_identity['creation_date']}
Interests: {', '.join(self.bot_identity['interests'])}"""

    async def run_ai(self, messages: List[Dict[str, str]]) -> str:
        """Run the AI model with given messages."""
        try:
            response = await self.client.post(
                f"{API_BASE_URL}@cf/meta/llama-3-8b-instruct",
                json={"messages": messages}
            )
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result and 'response' in result['result']:
                return result['result']['response']
            else:
                print(f"Unexpected API response structure: {result}")
                return "I encountered an error processing your request."
                
        except Exception as e:
            print(f"AI generation error: {e}")
            return "Sorry, I'm having trouble processing your request right now."

    def load_conversation_history(self, guild_id: int, limit: int = 5) -> list:
        """Load recent conversation history for a guild."""
        filepath = os.path.join(self.conversation_folder, f'conversation_{guild_id}.txt')
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                    return lines[-limit:] if lines else []
        except Exception as e:
            print(f"Error loading conversation history: {e}")
        return []

    def save_conversation_history(self, guild_id: int, conversation: str) -> None:
        """Append a conversation entry to history."""
        filepath = os.path.join(self.conversation_folder, f'conversation_{guild_id}.txt')
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"{conversation}\n")
        except Exception as e:
            print(f"Error saving conversation: {e}")

    @nextcord.slash_command(name='ask')
    async def ask_ai(self, interaction: nextcord.Interaction, question: str):
        """Process an AI question and return the response."""
        await interaction.response.defer()

        guild_id = str(interaction.guild_id)
        channel_id = self.guild_settings.get(guild_id, {}).get("channel_id")
        
        if channel_id and interaction.channel_id != channel_id:
            await interaction.followup.send(
                f"Please use the designated AI channel <#{channel_id}>",
                ephemeral=True
            )
            return

        try:
            user_id = str(interaction.user.id)
            user_name = (self.guild_settings.get(guild_id, {})
                        .get('user_names', {})
                        .get(user_id, interaction.user.display_name))

            # Prepare messages for the AI
            messages = [
                {"role": "system", "content": self.get_identity_prompt()},
            ]
            
            # Add recent conversation history
            history = self.load_conversation_history(interaction.guild_id)
            for entry in history:
                role = "assistant" if entry.startswith("AI: ") else "user"
                content = entry.split(": ", 1)[1] if ": " in entry else entry
                messages.append({"role": role, "content": content})
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Get AI response
            response = await self.run_ai(messages)
            
            # Save conversation entries
            self.save_conversation_history(interaction.guild_id, f"{user_name}: {question}")
            self.save_conversation_history(interaction.guild_id, f"AI: {response}")
            
            await interaction.followup.send(f"**{user_name}**: {response}")
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)
            await interaction.followup.send(
                "Sorry, I encountered an error while processing your request.",
                ephemeral=True
            )

    @nextcord.slash_command(name='set_name')
    async def set_name(self, interaction: nextcord.Interaction, name: str):
        """Set user's preferred name for AI interaction."""
        if not 2 <= len(name) <= 32:
            await interaction.response.send_message(
                "Name must be between 2 and 32 characters long.",
                ephemeral=True
            )
            return

        guild_id = str(interaction.guild_id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        if 'user_names' not in self.guild_settings[guild_id]:
            self.guild_settings[guild_id]['user_names'] = {}
            
        self.guild_settings[guild_id]['user_names'][str(interaction.user.id)] = name
        self._save_json_file(self.guild_settings_file, self.guild_settings)
        
        await interaction.response.send_message(
            f"Your name has been set to: {name}",
            ephemeral=True
        )

    @nextcord.slash_command(name='set_ai_channel')
    @commands.has_permissions(manage_channels=True)
    async def set_ai_channel(self, interaction: nextcord.Interaction):
        """Set the channel for AI responses."""
        guild_id = str(interaction.guild_id)
        
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        
        self.guild_settings[guild_id]["channel_id"] = interaction.channel_id
        self._save_json_file(self.guild_settings_file, self.guild_settings)
        
        await interaction.response.send_message(
            f"AI channel set to {interaction.channel.mention}",
            ephemeral=True
        )

def setup(bot):
    if API_BASE_URL and HEADERS["Authorization"]:
        print("[WARN]: Cannot load AI Chatbot due to improper configuration!")
    else:
        bot.add_cog(AICog(bot))
