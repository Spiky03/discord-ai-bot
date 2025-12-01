<div align="center">
    <h1>Discord AI Bot</h1>
    <h2>Repository is now in maintanance mode - rewriting project to Typescript on <a href="https://github.com/238SAMIxD/discord-ai-bot/tree/typescript">typescript</a> branch</h2>
    <h3 align="center">Discord bot to interact with <a href="https://github.com/jmorganca/ollama">Ollama</a> and <a href="https://github.com/AUTOMATIC1111/stable-diffusion-webui">AUTOMATIC1111 Stable Diffusion</a> as a chatbot</h3>
    <h3><img alt="Stars" src="https://img.shields.io/github/stars/mekb-turtle/discord-ai-bot?display_name=tag&style=for-the-badge" /></h3>
    <h3><img alt="Discord chat with the bot" src="assets/screenshot.png" /></h3>
</div>

The project started thanks to [mekb](https://github.com/mekb-turtle).

### Set-up instructions

1. Install [Node.js](https://nodejs.org) (if you have a package manager, use that instead to install this)
   - Make sure to install at least v14 of Node.js
2. Install [Ollama](https://github.com/jmorganca/ollama) (ditto)
3. Pull (download) a model, e.g `ollama pull orca` or `ollama pull llama2`
4. Start Ollama by running `ollama serve`
5. [Create a Discord bot](https://discord.com/developers/applications)
   - Under Application » Bot
     - Enable Message Content Intent
     - Enable Server Members Intent (for replacing user mentions with the username)
6. Invite the bot to a server
   1. Go to Application » OAuth2 » URL Generator
   2. Enable `bot`
   3. Enable Send Messages, Read Messages/View Channels, and Read Message History
   4. Under Generated URL, click Copy and paste the URL in your browser
<div align="center">
    <h1>Discord AI Bot</h1>
    <h2>Repository is now in maintanance mode - rewriting project to Typescript on <a href="https://github.com/238SAMIxD/discord-ai-bot/tree/typescript">typescript</a> branch</h2>
    <h3 align="center">Discord bot to interact with <a href="https://github.com/jmorganca/ollama">Ollama</a> and <a href="https://github.com/AUTOMATIC1111/stable-diffusion-webui">AUTOMATIC1111 Stable Diffusion</a> as a chatbot</h3>
    <h3><img alt="Stars" src="https://img.shields.io/github/stars/mekb-turtle/discord-ai-bot?display_name=tag&style=for-the-badge" /></h3>
    <h3><img alt="Discord chat with the bot" src="assets/screenshot.png" /></h3>
</div>

The project started thanks to [mekb](https://github.com/mekb-turtle).

# Discord AI Bot

A Discord bot that integrates with Ollama and Stable Diffusion to provide AI chat and image generation capabilities.

## Features

- **AI Chat**: Chat with LLMs via Ollama.
- **Image Generation**: Generate images using Stable Diffusion.
- **Context Awareness**: Maintains conversation context.
- **Multi-Model Support**: Switch between different Ollama models.

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) running locally or remotely.
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) (optional, for image generation).

## Installation

1.  Clone the repository.
2.  Copy `.env.example` to `.env` and configure your tokens and URLs.
3.  Run `start.bat` (Windows) or install requirements and run `main.py`.

```bash
pip install -r requirements.txt
python main.py
```

## Docker

You can also run the bot using Docker Compose:

```bash
docker compose up -d
```
