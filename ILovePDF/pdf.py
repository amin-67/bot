# This module is part of https://github.com/nabilanavab/ilovepdf
# Feel free to use and contribute to this project. Your contributions are welcome!
# copyright ©️ 2021 nabilanavab


file_name = "ILovePDF/pdf.py"

from configs.config import bot
from telebot import async_telebot
from logger import logger


# GLOBAL VARIABLES
PDF = {}  # save images for generating pdf
works = {"u": [], "g": []}  # broken works

# Initialize pyTgLovePDF only when API token is provided to avoid
# raising errors at import time (the main module checks for credentials).
pyTgLovePDF = None
if bot.API_TOKEN:
	try:
		pyTgLovePDF = async_telebot.AsyncTeleBot(bot.API_TOKEN, parse_mode="Markdown")
	except Exception as e:
		logger.debug(f"Failed to initialize AsyncTeleBot: {e}", exc_info=True)
else:
	logger.debug("AsyncTeleBot not created: API_TOKEN is missing.")


# If you have any questions or suggestions, please feel free to reach out.
# Together, we can make this project even better, Happy coding!  XD
