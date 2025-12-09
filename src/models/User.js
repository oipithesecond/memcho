const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  telegramChatId: { type: String, required: true, unique: true },
  googleRefreshToken: { type: String }, 
  timezone: { type: String, default: 'null' },
  isSetupComplete: { type: Boolean, default: false }
});

module.exports = mongoose.model('User', userSchema);