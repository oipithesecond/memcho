import sys
import datetime
from googleapiclient.discovery import build
from shared import db, bot, get_credentials_for_user
#scheduler

def check_timed_tasks():
    if not db or not bot:
        print("Database or Bot not initialized. Exiting timed task check.")
        return

    print(f"Running check_timed_tasks at {datetime.datetime.utcnow()} UTC")
    now = datetime.datetime.utcnow()
    fifteen_min_later = now + datetime.timedelta(minutes=15)
    
    try:
        users_cursor = db.users.find()
        
        for user in users_cursor:
            chat_id = user['chat_id']
            creds = get_credentials_for_user(chat_id)
            if not creds:
                print(f"Skipping user {chat_id}: No valid credentials.")
                continue
                
            service = build('tasks', 'v1', credentials=creds)
            sent_task_ids = user.get('sent_task_ids', [])
            
            try:
                results = service.tasks().list(
                    tasklist='@default',
                    dueMin=now.isoformat() + "Z",
                    dueMax=fifteen_min_later.isoformat() + "Z",
                    showCompleted=False
                ).execute()
                
                tasks = results.get('items', [])
                
                for task in tasks:
                    task_id = task['id']
                    if task_id not in sent_task_ids:
                        print(f"Sending timed reminder for task '{task['title']}' to user {chat_id}")
                        bot.send_message(
                            chat_id=chat_id,
                            text=f"Reminder: Your task '{task['title']}' is due soon!"
                        )
                        db.users.update_one(
                            {'chat_id': chat_id},
                            {'$push': {'sent_task_ids': task_id}}
                        )
                        
            except Exception as e:
                print(f"Error checking tasks for user {chat_id}: {e}")
                if 'invalid_grant' in str(e):
                    pass

    except Exception as e:
        print(f"Error fetching users from MongoDB: {e}")

def check_daily_tasks():
    """
    Cron Job 2: Checks for date-only tasks due tomorrow.
    Run this once per day (e.g., at 7:30 UTC: 30 7 * * *).
    """
    if not db or not bot:
        print("Database or Bot not initialized. Exiting daily task check.")
        return

    print(f"Running check_daily_tasks at {datetime.datetime.utcnow()} UTC")
    tomorrow = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        users_cursor = db.users.find()
        
        for user in users_cursor:
            chat_id = user['chat_id']
            creds = get_credentials_for_user(chat_id)
            if not creds:
                print(f"Skipping user {chat_id}: No valid credentials.")
                continue
                
            service = build('tasks', 'v1', credentials=creds)
            sent_task_ids = user.get('sent_task_ids', [])
            
            try:
                results = service.tasks().list(
                    tasklist='@default',
                    showCompleted=False,
                ).execute()
                
                tasks = results.get('items', [])
                
                for task in tasks:
                    due_date_str = task.get('due', '')
                    
                    if len(due_date_str) == 10 and due_date_str == tomorrow:
                        task_id = task['id']
                        if task_id not in sent_task_ids:
                            print(f"Sending daily reminder for task '{task['title']}' to user {chat_id}")
                            bot.send_message(
                                chat_id=chat_id,
                                text=f"Daily Reminder: Your task '{task['title']}' is due tomorrow."
                            )
                            db.users.update_one(
                                {'chat_id': chat_id},
                                {'$push': {'sent_task_ids': task_id}}
                            )

            except Exception as e:
                print(f"Error checking daily tasks for user {chat_id}: {e}")

    except Exception as e:
        print(f"Error fetching users from MongoDB: {e}")