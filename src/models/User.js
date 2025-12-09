const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  telegramChatId: { type: String, required: true, unique: true },
  googleRefreshToken: { type: String }, 
  timezone: { type: String, default: 'UTC' } 
});

module.exports = mongoose.model('User', userSchema);