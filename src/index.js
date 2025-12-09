const express = require('express');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const { createOAuthClient } = require('./services/google');
const User = require('./models/User');
const { bot, sendMessage } = require('./services/telegram');
const cronController = require('./controllers/cronController');

dotenv.config();
const app = express();
const PORT = process.env.PORT || 3000;

// Connect DB
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB Connected'))
  .catch(err => console.error(err));


// routes
// cron endpoint
app.get('/api/cron/tick', cronController.runTaskChecks);

// tele webhook
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  
  const oauth2Client = createOAuthClient();
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline', 
    scope: ['https://www.googleapis.com/auth/tasks.readonly'],
    state: chatId.toString() 
  });

  sendMessage(chatId, `Please authorize Google Tasks access here: ${authUrl}`);
});

// google auth callback
app.get('/auth/callback', async (req, res) => {
  const { code, state } = req.query; 
  const chatId = state;

  try {
    const oauth2Client = createOAuthClient();
    const { tokens } = await oauth2Client.getToken(code);
    
    // save or update user
    await User.findOneAndUpdate(
      { telegramChatId: chatId },
      { 
        telegramChatId: chatId,
        googleRefreshToken: tokens.refresh_token,
        // set timezone here. currently defaulting to UTC
      },
      { upsert: true, new: true }
    );

    sendMessage(chatId, "Successfully connected! I will now monitor your tasks.");
    res.send("Authentication successful! You can close this window.");
  } catch (error) {
    console.error('Auth Error', error);
    res.status(500).send("Authentication failed.");
  }
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});