from flask import request, redirect, session, url_for
import telegram
import os
from shared import app, bot, db, get_google_flow
# web server

@app.route('/')
def index():
    return "Bot server is running."

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    if not bot:
        return "Bot not configured", 500

    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    if update.message and update.message.text == '/start':
        chat_id = update.message.chat.id
        session['chat_id'] = chat_id
        
        keyboard = [[telegram.InlineKeyboardButton("Connect Google Tasks", callback_data='connect')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        
        bot.send_message(
            chat_id=chat_id, 
            text="Welcome! Please connect your Google Tasks account.",
            reply_markup=reply_markup
        )
        
    elif update.callback_query and update.callback_query.data == 'connect':
        chat_id = update.callback_query.message.chat.id
        session['chat_id'] = chat_id 
        
        flow = get_google_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',  
            prompt='consent'       
        )

        session['state'] = state
        
        bot.send_message(
            chat_id=chat_id, 
            text=f"Click this link to authorize:\n\n{authorization_url}\n\n"
                 "After authorizing, you will be redirected back here."
        )
        
    return 'ok', 200

@app.route('/auth/google/callback')
def auth_google_callback():
    """
    This is the REDIRECT_URI that Google sends the user back to
    after they have successfully authenticated.
    """
    state = session.get('state')
    chat_id = session.get('chat_id')
    
    if not state or not chat_id:
        return "Error: Session expired or invalid. Please try connecting again from Telegram.", 400
    
    if not db:
        return "Error: Database not connected.", 500

    try:
        flow = get_google_flow()
        flow.fetch_token(authorization_response=request.url)
        
        creds = flow.credentials
        refresh_token = creds.refresh_token
        
        if not refresh_token:
            bot.send_message(chat_id=chat_id, text="Error: A refresh token was not provided. Please try connecting again.")
            return "Error: A refresh token was not provided. Please re-authorize and ensure you are granting 'offline' access.", 400

        db.users.update_one(
            {'chat_id': chat_id},
            {'$set': {
                'chat_id': chat_id,
                'google_refresh_token': refresh_token
            },
             '$setOnInsert': {
                'sent_task_ids': [] 
             }},
            upsert=True
        )
        
        bot.send_message(chat_id=chat_id, text="Success! Your Google Tasks account is connected. You will now receive reminders.")
        return "Authentication successful! You can close this window."
    
    except Exception as e:
        print(f"Error in OAuth callback for {chat_id}: {e}")
        if 'chat_id' in locals():
             bot.send_message(chat_id=chat_id, text=f"Error saving your credentials: {e}")
        return "An error occurred. Please try again.", 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)