const TelegramBot = require('node-telegram-bot-api');
const GeoTz = require('geo-tz');
const User = require('../models/User');
require('dotenv').config();

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN);

const sendMessage = async (chatId, text) => {
  try {
    await bot.sendMessage(chatId, text);
  } catch (error) {
    console.error(`Failed to send telegram message to ${chatId}`, error);
  }
};

const askForLocation = async (chatId) => {
    const opts = {
      reply_markup: {
        keyboard: [
          [{
            text: "Share Location to Set Timezone",
            request_location: true
          }]
        ],
        resize_keyboard: true,
        one_time_keyboard: true
      }
    };
    await bot.sendMessage(chatId, "I need your timezone to send alerts at the right time. Please tap the button below:", opts);
};

bot.on('location', async (msg) => {
    const chatId = msg.chat.id;
    const { latitude, longitude } = msg.location;
  
    try {
      // get timezone from lat/lon
      const foundTimezones = GeoTz.find(latitude, longitude); 
      const timezone = foundTimezones[0]; 
  
      // save to db
      await User.findOneAndUpdate(
        { telegramChatId: chatId },
        { timezone: timezone, isSetupComplete: true }
      );
  
      await bot.sendMessage(chatId, `Timezone set to: ${timezone}.\nI will check your tasks every hour.`, {
        reply_markup: { remove_keyboard: true } 
      });
  
    } catch (error) {
      console.error('Location Error:', error);
      sendMessage(chatId, "Error setting timezone. Please try again.");
    }
});


module.exports = { bot, sendMessage };