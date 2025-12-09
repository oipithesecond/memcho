const TelegramBot = require('node-telegram-bot-api');
require('dotenv').config();

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN);

const sendMessage = async (chatId, text) => {
  try {
    await bot.sendMessage(chatId, text);
  } catch (error) {
    console.error(`Failed to send telegram message to ${chatId}`, error);
  }
};

module.exports = { bot, sendMessage };