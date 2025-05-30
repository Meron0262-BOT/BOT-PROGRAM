from threading import Thread
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from googletrans import Translator
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("Key")

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
BOT_OWNER_ID = 1234788478034645015
bot = commands.Bot(command_prefix="me!", intents=intents)

@bot.event
async def on_ready():
    print(f"ログイン成功！Bot名：{bot.user}")
    if not hasattr(bot, 'synced'):
        try:
            synced = await bot.tree.sync()
            bot.synced = True
            print(f"スラッシュコマンドを {len(synced)} 個同期しました！")
        except Exception as e:
            print(e)

# -----------------------------
# Slashコマンド（BOT作成者限定say）
@bot.tree.command(name="say", description="BOTがあなたの代わりに話してくれます！（BOT作成者専用）")
async def say(interaction: discord.Interaction, message: str):
    if interaction.user.id != BOT_OWNER_ID:
        await interaction.response.send_message("😭 このコマンドはBOT作成者専用です！", ephemeral=False)
        return
    await interaction.response.send_message(message)

# -----------------------------
# キックコマンド
@bot.tree.command(name="kick", description="指定したメンバーをキックします（サーバーオーナー専用）")
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = "なし"):
    if interaction.guild is None:
        await interaction.response.send_message("😭　このコマンドはサーバー内でのみ使用可能です！", ephemeral=False)
        return
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("😭　このコマンドはサーバーオーナーしか使えません！", ephemeral=False)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"{member.mention} をキックしました！理由: {reason}")

# -----------------------------
# BANコマンド
@bot.tree.command(name="ban", description="指定したメンバーをBANします（サーバーオーナー専用）")
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = "なし"):
    if interaction.guild is None:
        await interaction.response.send_message("😭　このコマンドはサーバー内でのみ使用可能です！", ephemeral=True)
        return
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("😭　このコマンドはサーバーオーナーしか使えません！", ephemeral=False)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member} をBANしました！理由: {reason}")

# -----------------------------
# タイムアウト
# --- スラッシュコマンド ---
@bot.tree.command(name="timeout", description="指定したメンバーをタイムアウトします（サーバーオーナー専用）")
@discord.app_commands.describe(
    member="タイムアウトするメンバー",
    duration="例: 10秒, 2分, 1時間",
    reason="理由（任意）"
)
async def timeout_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = None):
    if interaction.guild is None:
        await interaction.response.send_message("😭　このコマンドはサーバー内でのみ使用可能です！", ephemeral=True)
        return
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("😭　このコマンドはサーバーオーナーしか使えません！", ephemeral=False)
        return

    unit_multipliers = {'秒': 1, '分': 60, '時間': 3600}
    seconds = None
    for unit, multiplier in unit_multipliers.items():
        if duration.endswith(unit):
            try:
                number = int(duration.replace(unit, ''))
                seconds = number * multiplier
                break
            except ValueError:
                await interaction.response.send_message("時間の数値が間違っています！")
                return
    if seconds is None:
        await interaction.response.send_message("単位は「秒」「分」「時間」のどれかを使用してください！")
        return

    until_time = discord.utils.utcnow() + timedelta(seconds=seconds)
    try:
        await member.timeout(until_time)
        await interaction.response.send_message(f"{member.mention} を {duration} タイムアウトしました！理由: {reason or 'なし'}")
    except discord.Forbidden:
        await interaction.response.send_message("😭　BOTに権限がありません！")
    except Exception as e:
        await interaction.response.send_message("😭　タイムアウトに失敗しました！")
        print(e)

# --- テキストコマンド ---
@bot.command(name="timeout")
async def timeout_command(ctx, member: discord.Member, duration: str, *, reason: str = "なし"):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("このコマンドはサーバーオーナーしか使えません！")
        return

    unit_multipliers = {'秒': 1, '分': 60, '時間': 3600}
    seconds = None
    for unit, multiplier in unit_multipliers.items():
        if duration.endswith(unit):
            try:
                number = int(duration.replace(unit, ''))
                seconds = number * multiplier
                break
            except ValueError:
                await ctx.send("時間の数値が間違っています！")
                return
    if seconds is None:
        await ctx.send("単位は「秒」「分」「時間」のどれかを使ってね！")
        return

    until_time = discord.utils.utcnow() + timedelta(seconds=seconds)
    try:
        await member.timeout(until_time)
        await ctx.send(f"{member.mention} を {duration} タイムアウトしました！理由: {reason}")
    except discord.Forbidden:
        await ctx.send("😭　BOTに権限が付与されていません！")
    except Exception as e:
        await ctx.send("😭　タイムアウトに失敗しました！")
        print(e)

# メンションコマンド
@bot.tree.command(name="mention", description="指定したユーザーにメンションします（上限30回）")
async def mentionbomb(interaction: discord.Interaction, member: discord.Member, message: str, count: int):
    
    # サーバーオーナーかどうかチェック@bot.slash_command
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("😭　このコマンドはサーバーオーナーしか使えません！", ephemeral=False)
        return

    # メンションの回数上限チェック
    if count > 30:
        await interaction.response.send_message("😭　メンションの回数は最大30回までにしてください！", ephemeral=False)
        return

    # メッセージ送信
    mention_text = (f"{member.mention} {message}\n" * count).strip()
    await interaction.response.send_message(mention_text)

translator = Translator()

@bot.tree.command(name="translate", description="言葉を指定した言語に翻訳します！")
@discord.app_commands.describe(
    text="翻訳したいテキスト",
    target_lang="翻訳先の言語コード（例: en, ja）"
)
async def translate(interaction: discord.Interaction, text: str, target_lang: str):
    try:
        result = await translator.translate(text, dest=dest_lang)
        await interaction.response.send_message(
            f" 翻訳結果（{dest_lang}）:\n```{result.text}```"
        )
    except Exception as e:
        print(e)
        await interaction.response.send_message("😭　翻訳に失敗しました！")
        
# -----------------------------
# テキストコマンドのエラー処理
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("コマンドを使う権限がありません！")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("引数が足りません！")
    else:
        await ctx.send("エラーが発生しました！")
        print(error)

# -----------------------------
# 起動（トークンは環境変数などで安全に管理してね）
bot.run("TOKEN")
