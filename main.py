import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from src.bot import bot, TOKEN
    bot.run(TOKEN)
