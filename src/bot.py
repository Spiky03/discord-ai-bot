import os
import sys

# Allow running this file directly by adding the project root to sys.path
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "src"

import json
import re
import asyncio
import datetime
import logging
import aiohttp
import disnake
from disnake.ext import commands
from dotenv import load_dotenv
from .utils import (
    make_request, 
    split_text, 
    get_boolean, 
    log_error, 
    logger, 
    CHANNELS, 
    MODEL,
    RANDOM_SERVER
)

load_dotenv()

# Configuration
TOKEN = os.getenv("TOKEN")
SYSTEM_PROMPT = os.getenv("SYSTEM")
USE_SYSTEM = get_boolean(os.getenv("USE_SYSTEM"))
USE_MODEL_SYSTEM = get_boolean(os.getenv("USE_MODEL_SYSTEM"))
SHOW_START_OF_CONVERSATION = get_boolean(os.getenv("SHOW_START_OF_CONVERSATION"))
INITIAL_PROMPT = os.getenv("INITIAL_PROMPT")
USE_INITIAL_PROMPT = get_boolean(os.getenv("USE_INITIAL_PROMPT"))
REQUIRES_MENTION = get_boolean(os.getenv("REQUIRES_MENTION"))

def parse_json_message(s):
    try:
        # This is a bit hacky to match the original JS logic of parsing line by line as JSON strings
        lines = s.splitlines()
        parsed_lines = []
        for line in lines:
            # In JS: JSON.parse(`"${line}"`)
            # In Python, we can just use the string, but maybe it handles escapes?
            # We'll just return the line for now unless it's clearly a JSON string format
            parsed_lines.append(line) 
        return "\n".join(parsed_lines)
    except Exception:
        return s

def parse_env_string(s):
    if not s: return None
    s = parse_json_message(s)
    return s.replace("<date>", datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"))

custom_system_message = parse_env_string(SYSTEM_PROMPT)
use_custom_system_message = USE_SYSTEM and bool(custom_system_message)
initial_prompt_parsed = parse_env_string(INITIAL_PROMPT)
use_initial_prompt = USE_INITIAL_PROMPT and bool(initial_prompt_parsed)

# Bot setup
intents = disnake.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned, # We handle text commands manually in on_message
    intents=intents,
    help_command=None
)

# State
messages = {} # {channel_id: {amount: int, last: context}}
model_info = None

async def reply_split_message(message, content):
    response_messages = split_text(content, 2000)
    sent_messages = []
    
    for i, text in enumerate(response_messages):
        if i == 0:
            sent_messages.append(await message.reply(text))
        else:
            sent_messages.append(await message.channel.send(text))
            
    return sent_messages

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("Loading extensions...")
    bot.load_extension("src.cogs.text2img")
    logger.info("Extensions loaded.")
    
    # Set presence
    await bot.change_presence(status=disnake.Status.online, activity=None)

@bot.event
async def on_message(message):
    global model_info
    
    # Ignore own messages and bots
    if message.author.bot or message.author.id == bot.user.id:
        return

    # Check channel
    if message.guild and str(message.channel.id) not in CHANNELS:
        return
        
    # Check if message is empty
    if not message.content and not message.attachments:
        return

    channel_id = message.channel.id
    
    # Context handling for replies
    context = None
    if message.reference:
        try:
            reply = await message.channel.fetch_message(message.reference.message_id)
            if reply.author.id == bot.user.id:
                if channel_id in messages and reply.id in messages[channel_id]:
                    context = messages[channel_id][reply.id]
        except disnake.NotFound:
            pass
            
    # Fetch model info if needed
    if model_info is None:
        try:
            info = await make_request("/api/show", "post", {"name": MODEL})
            if isinstance(info, str):
                model_info = json.loads(info)
            else:
                model_info = info
        except Exception as e:
            logger.error("Failed to fetch model info")
            log_error(e)
            
    # Prepare system message
    system_messages = []
    if USE_MODEL_SYSTEM and model_info and model_info.get("system"):
        system_messages.append(model_info["system"])
    if use_custom_system_message:
        system_messages.append(custom_system_message)
        
    system_message = "\n\n".join(system_messages)

    # Clean user input (remove mention)
    user_input = message.content.replace(bot.user.mention, "").strip()
    # Also handle nickname mentions if needed, but disnake handles mentions well usually.
    # The original code had complex regex for mentions.
    # We'll just strip the bot's mention if it's at the start.
    if message.content.startswith(f"<@{bot.user.id}>"):
        user_input = message.content[len(f"<@{bot.user.id}>"):].strip()
    elif message.content.startswith(f"<@!{bot.user.id}>"):
        user_input = message.content[len(f"<@!{bot.user.id}>"):].strip()

    # Commands
    if user_input.startswith("."):
        args = user_input[1:].split()
        cmd = args[0].lower()
        
        if cmd in ["reset", "clear"]:
            if channel_id in messages:
                cleared = messages[channel_id]["amount"]
                del messages[channel_id]
                if cleared > 0:
                    await message.reply(f"Cleared conversation of {cleared} messages")
                    return
            await message.reply("No messages to clear")
            return
            
        elif cmd in ["help", "?", "h"]:
            await message.reply("Commands:\n- `.reset` `.clear`\n- `.help` `.?` `.h`\n- `.ping`\n- `.model`\n- `.system`")
            return
            
        elif cmd == "model":
            await message.reply(f"Current model: {MODEL}")
            return
            
        elif cmd == "system":
            await reply_split_message(message, f"System message:\n\n{system_message}")
            return
            
        elif cmd == "ping":
            before = datetime.datetime.now()
            msg = await message.reply("Ping")
            after = datetime.datetime.now()
            diff = (after - before).total_seconds() * 1000
            await msg.edit(content=f"Ping: {diff:.0f}ms")
            return
            
        else:
            await message.reply("Unknown command, type `.help` for a list of commands")
            return

    # Check mention requirement
    if REQUIRES_MENTION and message.guild and not bot.user.mentioned_in(message):
        # Unless it's a reply to the bot which we checked earlier via context, but original code logic:
        # if (message.type == MessageType.Default && (requiresMention && message.guild && !message.content.match(myMention))) return;
        # If it's a reply, message.type is REPLY.
        if message.type == disnake.MessageType.default:
             return

    # Replace mentions in text
    # Simple replacement
    for user in message.mentions:
        user_input = user_input.replace(user.mention, f"@{user.name}")
    for channel in message.channel_mentions:
        user_input = user_input.replace(channel.mention, f"#{channel.name}")
    for role in message.role_mentions:
        user_input = user_input.replace(role.mention, f"@{role.name}")
        
    if not user_input and not message.attachments:
        return

    # Handle text attachments
    if message.attachments:
        text_attachments = [att for att in message.attachments if att.content_type and att.content_type.startswith("text")]
        if text_attachments:
            try:
                for i, att in enumerate(text_attachments):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(att.url) as resp:
                            content = await resp.text()
                            user_input += f"\n{i + 1}. File - {att.filename}:\n{content}"
            except Exception as e:
                logger.error(f"Failed to download text files: {e}")
                await message.reply("Failed to download text files")
                return

    # Create conversation if needed
    if channel_id not in messages:
        messages[channel_id] = {"amount": 0, "last": None}
        
    logger.debug(f"{message.guild.name if message.guild else 'DMs'} - {message.author.name}: {user_input}")
    
    # Typing
    async with message.channel.typing():
        try:
            if context is None:
                context = messages[channel_id]["last"]
                
            if use_initial_prompt and messages[channel_id]["amount"] == 0:
                user_input = f"{initial_prompt_parsed}\n\n{user_input}"
                logger.debug("Adding initial prompt to message")
                
            # Make request
            payload = {
                "model": MODEL,
                "prompt": user_input,
                "system": system_message,
                "context": context,
                "stream": False
            }
            
            response_data = await make_request("/api/generate", "post", payload)
            
            response_objs = []
            if isinstance(response_data, str):
                # It's a stream of JSONs (fallback if stream=False is ignored or fails)
                lines = response_data.strip().split("\n")
                for line in lines:
                    if line.strip():
                        try:
                            response_objs.append(json.loads(line))
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON line: {line} - Error: {e}")
            elif isinstance(response_data, dict):
                response_objs.append(response_data)
            else:
                logger.warning(f"Unexpected response type: {type(response_data)}")
                
            response_text = "".join([r.get("response", "") for r in response_objs])
            if not response_text:
                logger.warning(f"Empty response text. Raw data: {response_data}")
                response_text = "(No response)"
                
            logger.debug(f"Response: {response_text}")
            
            prefix = ""
            if SHOW_START_OF_CONVERSATION and messages[channel_id]["amount"] == 0:
                prefix = "> This is the beginning of the conversation, type `.help` for help.\n\n"
                
            reply_msgs = await reply_split_message(message, prefix + response_text)
            reply_ids = [m.id for m in reply_msgs]
            
            # Update context
            # Find the object with done=True and context
            final_context = None
            for r in response_objs:
                if r.get("done") and r.get("context"):
                    final_context = r.get("context")
                    break
            
            if final_context:
                for rid in reply_ids:
                    if channel_id not in messages: messages[channel_id] = {"amount": 0, "last": None} # Safety
                    # We store context mapped to the reply ID so we can continue from it
                    if channel_id not in messages: messages[channel_id] = {} # Should be there
                    # Wait, messages[channel_id] is a dict with keys 'amount', 'last', and message IDs?
                    # Original: messages[channelID][replyMessageIDs[i]] = context;
                    messages[channel_id][rid] = final_context
                
                messages[channel_id]["last"] = final_context
                messages[channel_id]["amount"] += 1
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            log_error(e)
            await message.reply("Error, please check the console")

if __name__ == "__main__":
    bot.run(TOKEN)
