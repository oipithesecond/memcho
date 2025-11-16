import os
import datetime
import json
from flask import Flask
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests
import telegram
from pymongo import MongoClient
from dotenv import load_dotenv
# initialization

load_dotenv()

# --- General Setup ---
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    print("Warning: FLASK_SECRET_KEY is not set. Using a weak default.")
    app.secret_key = "YOUR_FALLBACK_SECRET_KEY_12345"

# --- Google OAuth Setup ---
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']
# This URL must be set in your Render Environment Variables
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if not RENDER_URL:
    print("Warning: RENDER_EXTERNAL_URL not set. Defaulting to localhost.")
    RENDER_URL = "http://127.0.0.1:8080"
REDIRECT_URI = RENDER_URL + "/auth/google/callback"

# Load the Google client config from an environment variable
GOOGLE_CLIENT_SECRET_JSON_STRING = os.environ.get("GOOGLE_CLIENT_SECRET_JSON")

def get_google_flow():
    """Helper function to create a Google OAuth Flow object."""
    if not GOOGLE_CLIENT_SECRET_JSON_STRING:
        raise ValueError("GOOGLE_CLIENT_SECRET_JSON environment variable not set.")
    
    try:
        # Parse the JSON string from the environment variable
        client_config = json.loads(GOOGLE_CLIENT_SECRET_JSON_STRING)
    except json.JSONDecodeError:
        raise ValueError("Failed to decode GOOGLE_CLIENT_SECRET_JSON. Check the variable.")
    
    # Use from_client_config instead of from_client_secrets_file
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# --- Telegram Bot Initialization ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("Warning: BOT_TOKEN environment variable not set.")
    bot = None
else:
    bot = telegram.Bot(token=BOT_TOKEN)

# --- MongoDB Atlas Initialization ---
MONGO_URI = os.environ.get("MONGO_URI")
db = None
if not MONGO_URI:
    print("Warning: MONGO_URI environment variable not set.")
else:
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client.get_database("telegram_bot_db")
        db.command('ping')
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        db = None

# --- Shared Helper Functions ---

def get_credentials_for_user(chat_id):
    """
    Fetches a user's refresh token from MongoDB and returns a valid
    Google API Credentials object.
    """
    if not db:
        print("Error: Database not connected.")
        return None

    user_data = db.users.find_one({'chat_id': int(chat_id)})
    if not user_data:
        print(f"No user data found for chat_id: {chat_id}")
        return None
        
    refresh_token = user_data.get('google_refresh_token')
    if not refresh_token:
        print(f"No refresh token found for user: {chat_id}")
        return None
    
    # Recreate credentials from the refresh token and client config
    if not GOOGLE_CLIENT_SECRET_JSON_STRING:
        print("Error: GOOGLE_CLIENT_SECRET_JSON env var not set.")
        return None
    
    try:
        client_config = json.loads(GOOGLE_CLIENT_SECRET_JSON_STRING).get('web', {})
    except json.JSONDecodeError:
        print("Error: Could not decode GOOGLE_CLIENT_SECRET_JSON.")
        return None
    
    client_id = client_config.get('client_id')
    client_secret = client_config.get('client_secret')
    token_uri = client_config.get('token_uri', 'https://oauth2.googleapis.com/token')

    if not client_id or not client_secret:
        print(f"client_id or client_secret missing from config for user {chat_id}")
        return None

    try:
        creds = Credentials(
            token=None, # No access token, we will refresh for it
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        # Refresh the token to get a new access_token
        creds.refresh(google.auth.transport.requests.Request())
        return creds
    except Exception as e:
        print(f"Error refreshing credentials for user {chat_id}: {e}")
        # This often happens if the user revoked access in their Google account
        return None