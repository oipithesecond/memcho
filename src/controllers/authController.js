const User = require('../models/User');
const { createOAuthClient } = require('../services/google');
const { sendMessage, askForLocation } = require('../services/telegram');

exports.handleAuthCallback = async (req, res) => {
  const { code, state } = req.query; 
  const chatId = state; 

  try {
    const oauth2Client = createOAuthClient();
    const { tokens } = await oauth2Client.getToken(code);

    // update user 
    await User.findOneAndUpdate(
      { telegramChatId: chatId },
      { googleRefreshToken: tokens.refresh_token },
      { upsert: true }
    );

    res.send("<h1>Connected! You can close this window and go back to Telegram.</h1>");
    
    // prompt for timezone 
    await sendMessage(chatId, "Google Account Connected!");
    await askForLocation(chatId);

  } catch (error) {
    console.error('Auth Error:', error);
    res.status(500).send("Authentication failed. Please try again.");
  }
};