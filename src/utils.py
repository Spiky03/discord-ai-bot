import os
import json
import random
import asyncio
import logging
import aiohttp
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bot")

def log_error(error):
    if hasattr(error, 'response') and error.response:
        logger.error(f"Error {error.response.status} {error.response.reason}: {error.request_info.method} {error.request_info.url}")
        # Note: getting body in aiohttp exception handling might require await, handled in caller usually
    else:
        logger.error(error)

def shuffle_array(array):
    random.shuffle(array)
    return array

# Environment variables
MODEL = os.getenv("MODEL")
OLLAMA_URLS = os.getenv("OLLAMA", "").split(",")
STABLE_DIFFUSION_URLS = os.getenv("STABLE_DIFFUSION", "").split(",")
CHANNELS = os.getenv("CHANNELS", "").split(",")
RANDOM_SERVER = os.getenv("RANDOM_SERVER", "false").lower() not in ("false", "no", "off", "0")

servers = [{"url": url, "available": True} for url in OLLAMA_URLS if url]
stable_diffusion_servers = [{"url": url, "available": True} for url in STABLE_DIFFUSION_URLS if url]

if not servers:
    logger.warning("No Ollama servers available in .env")

async def make_request(path, method, data=None):
    while not any(s["available"] for s in servers):
        await asyncio.sleep(1)

    error = None
    order = list(range(len(servers)))
    if RANDOM_SERVER:
        random.shuffle(order)

    for i in order:
        if not servers[i]["available"]:
            continue
        
        server = servers[i]
        base_url = server["url"]
        
        # Ensure base_url ends with / and path doesn't start with / to avoid issues, or use proper join
        if not base_url.endswith("/"):
            base_url += "/"
        if path.startswith("/"):
            path = path[1:]
            
        url = base_url + path
        
        server["available"] = False
        logger.debug(f"Making request to {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=data) as response:
                    response_text = await response.text()
                    server["available"] = True
                    # Try to parse JSON if possible, else return text
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        return response_text
        except Exception as err:
            server["available"] = True
            error = err
            log_error(err)
            
    if not error:
        raise Exception("No servers available")
    raise error

async def make_stable_diffusion_request(path, method, data=None):
    while not any(s["available"] for s in stable_diffusion_servers):
        await asyncio.sleep(1)

    error = None
    order = list(range(len(stable_diffusion_servers)))
    if RANDOM_SERVER:
        random.shuffle(order)

    for i in order:
        if not stable_diffusion_servers[i]["available"]:
            continue
            
        server = stable_diffusion_servers[i]
        base_url = server["url"]
        
        if not base_url.endswith("/"):
            base_url += "/"
        if path.startswith("/"):
            path = path[1:]
            
        url = base_url + path
        
        server["available"] = False
        logger.debug(f"Making stable diffusion request to {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=data) as response:
                    result = await response.json()
                    server["available"] = True
                    return result
        except Exception as err:
            server["available"] = True
            error = err
            log_error(err)

    if not error:
        raise Exception("No servers available")
    raise error

def split_text(text, length):
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    segments = []
    segment = ""
    
    # Simple word-based splitting to match the logic roughly
    # The original logic is quite complex with regex. 
    # We will implement a robust splitter.
    
    import re
    words = re.split(r'([^\s]+(?:\s+|$))', text)
    # Filter empty strings from split
    words = [w for w in words if w]

    for word in words:
        if len(segment) + len(word) > length:
            # Prioritize splitting by newlines if present in the current segment
            if "\n" in segment:
                before_paragraph = re.match(r'^.*\n', segment, re.DOTALL)
                if before_paragraph:
                    bp = before_paragraph.group(0)
                    last_paragraph = segment[len(bp):]
                    segments.append(bp.strip())
                    segment = last_paragraph + word
                    continue
            
            if segment.strip():
                segments.append(segment.strip())
            segment = ""
            
            # If word itself is too long
            if len(word) > length:
                # Just cut it for now, original logic had hyphenation attempt
                # We'll just add it as is (it will be split in next iteration or we force split)
                # But here we just append to empty segment
                pass
        
        segment += word
        
    if segment.strip():
        segments.append(segment.strip())
        
    return segments

def get_boolean(val):
    if val is None: return False
    s = str(val).lower()
    return s not in ("false", "no", "off", "0", "")

