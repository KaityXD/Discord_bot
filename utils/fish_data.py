# fish_data.py

# Fish tiers and their catch rates
tiers = {
    'junk': 0.15,      # 15% chance
    'common': 0.40,    # 40% chance
    'uncommon': 0.25,  # 25% chance
    'rare': 0.12,      # 12% chance
    'epic': 0.06,      # 6% chance
    'legendary': 0.02, # 2% chance
    'Mommy': 0.001     # 0.1% chance
}

# Fish data: name, min_price, max_price, tier
fish_data = {
    # Junk tier (funny items)
    "👟 Old Boot": (1, 5, 'junk'),
    "🧦 Wet Sock": (1, 3, 'junk'),
    "📱 Broken Phone": (5, 15, 'junk'),
    "🎮 Waterlogged Gaming Console": (10, 20, 'junk'),
    "🗑️ Literal Trash": (1, 2, 'junk'),
    "🚘 Rusty Car Part": (10, 25, 'junk'),
    "🍌 Banana Peel": (1, 2, 'junk'),
    "🪣 Broken Bucket": (1, 3, 'junk'),

    # Common tier
    "🐟 Small Fish": (10, 30, 'common'),
    "🐠 Colorful Fish": (15, 35, 'common'),
    "🎣 Tiny Bass": (20, 40, 'common'),
    "🐡 Baby Pufferfish": (25, 45, 'common'),
    "🐤 Duck": (30, 50, 'common'),
    "🦐 Shrimp": (15, 35, 'common'),
    "🦀 Crab": (25, 45, 'common'),
    "🐟 Sardine": (5, 25, 'common'),
    "🐙 Small Octopus": (20, 40, 'common'),

    # Uncommon tier
    "🐸 Frog": (50, 100, 'uncommon'),
    "🦈 Baby Shark": (75, 150, 'uncommon'),
    "🐢 Turtle": (100, 200, 'uncommon'),
    "🦦 Otter": (125, 225, 'uncommon'),
    "🦆 Golden Duck": (150, 250, 'uncommon'),
    "🐙 Octopus": (100, 200, 'uncommon'),
    "🐊 Small Crocodile": (125, 225, 'uncommon'),

    # Rare tier
    "🐋 Whale": (300, 600, 'rare'),
    "🐳 Blue Whale": (400, 800, 'rare'),
    "🦑 Giant Squid": (500, 1000, 'rare'),
    "🐊 Crocodile": (600, 1200, 'rare'),
    "🦈 Great White Shark": (700, 1400, 'rare'),
    "🐅 Tiger Shark": (500, 1000, 'rare'),
    "🦈 Hammerhead Shark": (600, 1200, 'rare'),

    # Epic tier
    "🐉 Dragon Fish": (1000, 2000, 'epic'),
    "⭐ Starfish Emperor": (1500, 3000, 'epic'),
    "🌈 Rainbow Fish": (2000, 4000, 'epic'),
    "🌟 Celestial Fish": (2500, 5000, 'epic'),
    "🦩 Mystical Flamingo": (1800, 3600, 'epic'),
    "🐲 Leviathan": (2000, 4000, 'epic'),

    # Legendary tier
    "💎 Diamond Fish": (5000, 10000, 'legendary'),
    "👑 Crown Fish": (7500, 15000, 'legendary'),
    "🔱 Poseidon's Pet": (10000, 20000, 'legendary'),
    "🌞 Sun Fish": (12500, 25000, 'legendary'),
    "🌊 Ocean's Spirit": (15000, 30000, 'legendary'),
    "🦚 Phoenix Fish": (20000, 40000, 'legendary'),

    # Mommy tier
    "🤰 Pregnant Mommy Fish": (100000, 250000, 'Mommy')
}

# Fun modifiers with special effects
modifiers = {
    'shiny': {'chance': 0.08, 'multiplier': 2.0, 'prefix': '✨'},
    'golden': {'chance': 0.05, 'multiplier': 3.0, 'prefix': '🌟'},
    'rainbow': {'chance': 0.03, 'multiplier': 4.0, 'prefix': '🌈'},
    'cursed': {'chance': 0.07, 'multiplier': 0.5, 'prefix': '👻'},
    'giant': {'chance': 0.04, 'multiplier': 5.0, 'prefix': '🔱'},
    'tiny': {'chance': 0.08, 'multiplier': 0.7, 'prefix': '🔍'},
    'ancient': {'chance': 0.02, 'multiplier': 10.0, 'prefix': '⚱️'},
    'blessed': {'chance': 0.01, 'multiplier': 20.0, 'prefix': '🌌'}
}

# Special events that can occur while fishing
special_events = [
    "You found a treasure chest! Extra 500 coins! 💎",
    "A friendly dolphin helped you fish! Double earnings! 🐬",
    "You caught two fish at once! Double earnings! 🎣",
    "A mermaid blessed your fishing rod! Triple earnings! 🧜‍♀️",
    "The fish was wearing tiny glasses! Extra 200 coins! 👓",
    "This fish knows how to dance! Extra 300 coins! 💃",
    "You found a message in a bottle! Extra 100 coins! 📜",
    "An ancient artifact washed up! Extra 1000 coins! ⚱️",
    "A rare pearl was hidden in the fish! Extra 500 coins! 🦪",
    "A pirate ghost appeared and shared treasure! Double earnings! 🏴‍☠️"
]

