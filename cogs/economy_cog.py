import nextcord
from nextcord.ext import commands
from tinydb import TinyDB, Query
import random
import time
from typing import Optional
import os
import asyncio

os.makedirs('database', exist_ok=True)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = TinyDB('database/economy.json')
        self.User = Query()

    def get_user_data(self, user_id: int):
        user = self.db.get(self.User.user_id == user_id)
        if not user:
            user = {
                'user_id': user_id,
                'wallet': 0,
                'bank': 0,
                'bank_capacity': 1000,
                'last_daily': 0,
                'last_work': 0,
                'inventory': []
            }
            self.db.insert(user)
        return user

    @commands.command(name="balance", aliases=["bal", "money"])
    async def balance(self, ctx, member: Optional[nextcord.Member] = None):
        target = member or ctx.author
        data = self.get_user_data(target.id)
        embed = nextcord.Embed(title=f"{target.name}'s Balance", color=0x00ff00)
        embed.add_field(name="Wallet", value=f"💰 {data['wallet']}")
        embed.add_field(name="Bank", value=f"🏦 {data['bank']}/{data['bank_capacity']}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        data = self.get_user_data(ctx.author.id)
        if amount.lower() == "all":
            amount = data['wallet']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("Please enter a valid amount!")
                return

        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        if amount > data['wallet']:
            await ctx.send("You don't have that much money!")
            return
        if data['bank'] + amount > data['bank_capacity']:
            await ctx.send("Your bank cannot hold that much!")
            return

        self.db.update({
            'wallet': data['wallet'] - amount,
            'bank': data['bank'] + amount
        }, self.User.user_id == ctx.author.id)
        await ctx.send(f"Successfully deposited 💰 {amount}!")

    @commands.command(aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        data = self.get_user_data(ctx.author.id)
        if amount.lower() == "all":
            amount = data['bank']
        else:
            try:
                amount = int(amount)
            except ValueError:
                await ctx.send("Please enter a valid amount!")
                return

        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        if amount > data['bank']:
            await ctx.send("You don't have that much money in your bank!")
            return

        self.db.update({
            'wallet': data['wallet'] + amount,
            'bank': data['bank'] - amount
        }, self.User.user_id == ctx.author.id)
        await ctx.send(f"Successfully withdrew 💰 {amount}!")

    @commands.command(aliases=["daily"])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def claim_daily(self, ctx):
        reward = random.randint(100, 500)
        data = self.get_user_data(ctx.author.id)
        self.db.update({
            'wallet': data['wallet'] + reward,
            'last_daily': time.time()
        }, self.User.user_id == ctx.author.id)
        await ctx.send(f"You claimed your daily reward of 💰 {reward}!")

    @commands.command(aliases=["steal", "rob"])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def heist(self, ctx, target: nextcord.Member):
        if target.id == ctx.author.id:
            await ctx.send("You can't rob yourself!")
            return

        thief_data = self.get_user_data(ctx.author.id)
        target_data = self.get_user_data(target.id)
        
        if target_data['wallet'] < 100:
            await ctx.send("Target doesn't have enough money to steal!")
            return
        
        if thief_data['wallet'] < 1000:
            await ctx.send("You need at least 💰 1000 to attempt a heist!")
            return

        success = random.random() < 0.4
        
        if success:
            steal_amount = random.randint(1, min(target_data['wallet'], 1000))
            self.db.update({
                'wallet': thief_data['wallet'] + steal_amount
            }, self.User.user_id == ctx.author.id)
            self.db.update({
                'wallet': target_data['wallet'] - steal_amount
            }, self.User.user_id == target.id)
            await ctx.send(f"Heist successful! You stole 💰 {steal_amount}!")
        else:
            fine = random.randint(500, 1000)
            self.db.update({
                'wallet': thief_data['wallet'] - fine
            }, self.User.user_id == ctx.author.id)
            await ctx.send(f"Heist failed! You were fined 💰 {fine}!")

    @commands.command(aliases=["givemoney", "pay"])
    async def transfer(self, ctx, target: nextcord.Member, amount: int):
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
            
        sender_data = self.get_user_data(ctx.author.id)
        if amount > sender_data['wallet']:
            await ctx.send("You don't have enough money!")
            return
            
        receiver_data = self.get_user_data(target.id)
        
        self.db.update({
            'wallet': sender_data['wallet'] - amount
        }, self.User.user_id == ctx.author.id)
        self.db.update({
            'wallet': receiver_data['wallet'] + amount
        }, self.User.user_id == target.id)
        
        await ctx.send(f"Successfully transferred 💰 {amount} to {target.name}!")

    @commands.command(aliases=["work", "job"])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def earn(self, ctx):
        earnings = random.randint(50, 200)
        data = self.get_user_data(ctx.author.id)
        
        self.db.update({
            'wallet': data['wallet'] + earnings,
            'last_work': time.time()
        }, self.User.user_id == ctx.author.id)
        
        jobs = ["programmer", "teacher", "chef", "driver", "artist"]
        job = random.choice(jobs)
        
        await ctx.send(f"You worked as a {job} and earned 💰 {earnings}!")

    @commands.command(aliases=["shop"])
    async def store(self, ctx):
        items = [
            {"name": "Fishing Rod", "price": 500, "id": "rod"},
            {"name": "Laptop", "price": 2000, "id": "laptop"},
            {"name": "Bank Upgrade", "price": 5000, "id": "bank_upgrade"}
        ]
        
        embed = nextcord.Embed(title="Store", description="Available items:", color=0x00ff00)
        for item in items:
            embed.add_field(name=item["name"], value=f"Price: 💰 {item['price']}\nID: {item['id']}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(aliases=["purchase"])
    async def buy(self, ctx, item_id: str):
        items = {
            "rod": {"name": "Fishing Rod", "price": 500},
            "laptop": {"name": "Laptop", "price": 2000},
            "bank_upgrade": {"name": "Bank Upgrade", "price": 5000}
        }
        
        if item_id not in items:
            await ctx.send("Invalid item ID!")
            return
            
        item = items[item_id]
        data = self.get_user_data(ctx.author.id)
        
        if data['wallet'] < item['price']:
            await ctx.send("You don't have enough money!")
            return
            
        if item_id == "bank_upgrade":
            self.db.update({
                'wallet': data['wallet'] - item['price'],
                'bank_capacity': data['bank_capacity'] + 5000
            }, self.User.user_id == ctx.author.id)
            await ctx.send(f"You purchased a bank upgrade! New capacity: 💰 {data['bank_capacity'] + 5000}")
        else:
            inventory = data.get('inventory', [])
            inventory.append(item_id)
            self.db.update({
                'wallet': data['wallet'] - item['price'],
                'inventory': inventory
            }, self.User.user_id == ctx.author.id)
            await ctx.send(f"You purchased a {item['name']}!")

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx):
        data = self.get_user_data(ctx.author.id)
        inventory = data.get('inventory', [])
        
        if not inventory:
            await ctx.send("Your inventory is empty!")
            return
            
        item_counts = {}
        for item in inventory:
            item_counts[item] = item_counts.get(item, 0) + 1
            
        embed = nextcord.Embed(title=f"{ctx.author.name}'s Inventory", color=0x00ff00)
        for item, count in item_counts.items():
            embed.add_field(name=item.title(), value=f"Quantity: {count}", inline=False)
            
        await ctx.send(embed=embed)

    @commands.command(aliases=["bet"])
    @commands.cooldown(300, 30, commands.BucketType.user)
    async def gamble(self, ctx, amount: int):
        data = self.get_user_data(ctx.author.id)
        
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        if amount > data['wallet']:
            await ctx.send("You don't have enough money!")
            return
            
        if random.random() < 0.45:
            winnings = amount * 2
            self.db.update({
                'wallet': data['wallet'] + amount
            }, self.User.user_id == ctx.author.id)
            await ctx.send(f"🎰 You won! Your reward: 💰 {winnings}")
        else:
            self.db.update({
                'wallet': data['wallet'] - amount
            }, self.User.user_id == ctx.author.id)
            await ctx.send("🎰 You lost! Better luck next time!")

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        all_users = self.db.all()
        sorted_users = sorted(all_users, 
                            key=lambda x: x.get('wallet', 0) + x.get('bank', 0), 
                            reverse=True)[:10]
        
        embed = nextcord.Embed(title="Richest Users", color=0x00ff00)
        for idx, user in enumerate(sorted_users, 1):
            user_obj = self.bot.get_user(user['user_id'])
            if user_obj:
                total = user.get('wallet', 0) + user.get('bank', 0)
                embed.add_field(
                    name=f"{idx}. {user_obj.name}",
                    value=f"Total: 💰 {total}",
                    inline=False
                )
        await ctx.send(embed=embed)

    @commands.command(aliases=["sl"])
    @commands.cooldown(300, 30, commands.BucketType.user)
    async def slots(self, ctx, amount: int):
        data = self.get_user_data(ctx.author.id)
        
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        if amount > data['wallet']:
            await ctx.send("You don't have enough money!")
            return
            
        emojis = ["🍎", "🍊", "🍇", "🍒", "💎", "7️⃣"]
        slots = [random.choice(emojis) for _ in range(3)]
        
        result = " | ".join(slots)
        await ctx.send(f"🎰 Spinning...\n{result}")
        
        if len(set(slots)) == 1:
            winnings = amount * 5
            message = f"JACKPOT! You won 💰 {winnings}!"
        elif len(set(slots)) == 2:
            winnings = amount * 2
            message = f"Two of a kind! You won 💰 {winnings}!"
        else:
            winnings = -amount
            message = "No match! Better luck next time!"
            
        self.db.update({
            'wallet': data['wallet'] + winnings
        }, self.User.user_id == ctx.author.id)
        await ctx.send(message)


    @commands.command(aliases=["upgrade"])
    async def upgrade_bank(self, ctx):
        data = self.get_user_data(ctx.author.id)
        current_capacity = data['bank_capacity']
        
        upgrades = [
            {"capacity": 5000, "price": 5000},
            {"capacity": 10000, "price": 8000},
            {"capacity": 25000, "price": 15000},
            {"capacity": 50000, "price": 25000},
            {"capacity": 100000, "price": 50000}
        ]

def setup(bot):
    bot.add_cog(Economy(bot))


