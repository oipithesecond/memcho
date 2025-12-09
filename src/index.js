const express = require('express');
const mongoose = require('mongoose');
const dotenv = require('dotenv');
const { bot, sendMessage } = require('./services/telegram');
const { createOAuthClient } = require('./services/google');
const authController = require('./controllers/authController');
const cronController = require('./controllers/cronController');

dotenv.config();
const app = express();
app.use(express.json());
const PORT = process.env.PORT || 3000;

// db connection
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB Connected'))
  .catch(err => console.error(err));


//routes
app.get('/api/cron/tick', cronController.runTaskChecks);
app.get('/auth/callback', authController.handleAuthCallback);

app.post('/api/telegram', (req, res) => {
    const { body } = req;
    bot.processUpdate(body);
    res.sendStatus(200);
  });

// tele commands
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  
  const oauth2Client = createOAuthClient();
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: ['https://www.googleapis.com/auth/tasks.readonly'],
    state: chatId.toString() // pass chatId in state
  });

  sendMessage(chatId, `👋 Welcome! To get started, I need access to your Google Tasks.\n\n[Click here to Authorize](${authUrl})`, { parse_mode: 'Markdown' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});