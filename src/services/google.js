const { google } = require('googleapis');
require('dotenv').config();

const createOAuthClient = () => {
  return new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
  );
};

const getTasksClient = (refreshToken) => {
  const oauth2Client = createOAuthClient();
  oauth2Client.setCredentials({ refresh_token: refreshToken });
  return google.tasks({ version: 'v1', auth: oauth2Client });
};

module.exports = { createOAuthClient, getTasksClient };