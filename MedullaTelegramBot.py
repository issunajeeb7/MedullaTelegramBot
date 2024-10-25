from datetime import timedelta
import logging
import time
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import threading
import datetime

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Firebase setup
cred = credentials.Certificate(r"credentials.json")  # Update this path to your credentials file
firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to check if a user is a member of any group
def is_user_in_group(user_id, context: CallbackContext):
    groups_ref = db.collection('groups')
    groups = groups_ref.stream()
    group_ids = [group.to_dict().get('group_id') for group in groups]

    for group_id in group_ids:
        try:
            member = context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except Exception as e:
            logger.warning(f"Error checking membership in group {group_id}: {e}")
    return False


# Function to set the bot commands
def set_bot_commands(updater: Updater):
    # Define a list of bot commands
    commands = [
        BotCommand("start", "Start the bot and show the main menu"),
        BotCommand("services", "Show available services"),
        BotCommand("show_leaderboard", "Display the leaderboard"),
    ]
    
    # Set the commands for the bot
    updater.bot.set_my_commands(commands)

# Start command
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Services", callback_data='services')],
        [InlineKeyboardButton("Groups", callback_data='groups')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:  # Check if this is a regular message
        update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)
    elif update.callback_query:  # If it's a callback query
        query = update.callback_query
        query.answer()  # Acknowledge the callback
        query.edit_message_text(text="Welcome! Choose an option:", reply_markup=reply_markup)

    
def return_to_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Services", callback_data='services')],
        [InlineKeyboardButton("Groups", callback_data='groups')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:  # Check if this is a regular message
        update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)
    elif update.callback_query:  # If it's a callback query
        query = update.callback_query
        query.answer()  # Acknowledge the callback
        query.edit_message_text(text="Welcome! Choose an option:", reply_markup=reply_markup)

def return_to_services_menu(update: Update, context: CallbackContext):
    show_services(update, context)  # Pass 'update' directly
  # This will show the services menu


# Button handler
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    logger.debug(f"Button pressed: {query.data}")  # Debug print
    if query.data == 'services':
        show_services(update,context)
    elif query.data == 'groups':
        show_groups(query)
    elif query.data == 'pomodoro':
        show_pomodoro_options(query)
    elif query.data == 'simple_timer':
        simple_timer(update, context)
    elif query.data in ['pomodoro_5', 'pomodoro_15', 'pomodoro_25', 'start_sprint']:
        handle_pomodoro_selection(update, context)  # Call the function here directly for testing
    elif query.data == 'cancel_timer':
        handle_cancel(update, context)
    elif query.data == 'pomodoro_stats':
        show_stats(update, context)
    elif query.data == 'show_leaderboard':  
        show_leaderboard(update, context)
    elif query.data == 'back_to_start':  # Handle back to main menu
        return_to_main_menu(update, context)  # Call function to show main menu
    elif query.data == 'back_to_services':  # Handle back to services menu
        return_to_services_menu(update, context)  # Call function to show services menu



def show_services(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Pomodoro Timer", callback_data='pomodoro')],
        [InlineKeyboardButton("Stop Watch", callback_data='simple_timer')],
        [InlineKeyboardButton("Show Leaderboard", callback_data='show_leaderboard')],
        [InlineKeyboardButton("Back", callback_data='back_to_start')]  # Back button to main menu
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update, Update) and update.callback_query:  # Check if 'update' has 'callback_query'
        query = update.callback_query
        query.edit_message_text(text="Choose a service:", reply_markup=reply_markup)
    else:
        update.message.reply_text("Choose a service:", reply_markup=reply_markup)



# fetch groups from firestore and display them
def show_groups(query):
    groups_ref = db.collection('groups')
    groups = groups_ref.get()

    keyboard = []
    for group in groups:
        group_data = group.to_dict()
        group_name = group_data.get('group_name')
        group_username = group_data.get('group_username')
        group_url = f"https://t.me/{group_username}"
        logger.info(f"Group URL: {group_url}")
        keyboard.append([InlineKeyboardButton(group_name, url=group_url)])
    
    # Add a button to go back to the services menu
    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data='back_to_services')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(text="Join one of the groups:", reply_markup=reply_markup)

# Show Pomodoro options
# Show Pomodoro options
def show_pomodoro_options(query):
    keyboard = [
        [InlineKeyboardButton("5 min", callback_data='pomodoro_5')],
        [InlineKeyboardButton("15 min", callback_data='pomodoro_15')],
        [InlineKeyboardButton("25 min", callback_data='pomodoro_25')],
        [InlineKeyboardButton("Start Sprint (1h 55m)", callback_data='start_sprint')],
        [InlineKeyboardButton("Stats", callback_data='pomodoro_stats')],
        [InlineKeyboardButton("Stop Timer", callback_data='cancel_timer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Choose Pomodoro duration or action:", reply_markup=reply_markup)
    
# def show_services(update: Update, context: CallbackContext):
#     keyboard = [
#         [InlineKeyboardButton("Pomodoro Timer", callback_data='pomodoro')],
#         [InlineKeyboardButton("Stop Watch", callback_data='simple_timer')],
#         [InlineKeyboardButton("Show Leaderboard", callback_data='show_leaderboard')],
#         [InlineKeyboardButton("Back", callback_data='back_to_start')]  # Back button to main menu
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     if update.callback_query:
#         query = update.callback_query
#         query.edit_message_text(text="Choose a service:", reply_markup=reply_markup)
#     else:
#         update.message.reply_text("Choose a service:", reply_markup=reply_markup)

# Pomodoro timer functionality
def pomodoro_timer(update: Update, context: CallbackContext, duration):
    user = update.effective_user
    username = user.username
    user_id = user.id

    if not is_user_in_group(user_id, context):
        update.callback_query.edit_message_text("You must be a member of at least one group to use this service.")
        show_groups(update.callback_query)
        return

    users_ref = db.collection('users').document(username)
    users_ref.set({'username': username, 'is_active': True, 'timer_type': 'pomodoro', 'start_time': time.time()}, merge=True)
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    
    if hours > 0:
        total_time = f"{hours} hours, {minutes} minutes and {seconds} seconds"
    elif minutes > 0:
        total_time = f"{minutes} minutes and {seconds} seconds"
    else:
        total_time = f"{seconds} seconds"
        
    context.bot.send_message(chat_id=user_id, text=f"🔥 Pomodoro started, {username}! ⏳ Stay focused for the next {total_time}. You've got this! 💪🚀")
    get_active_user_count(update, context)

    # Start the timer in a separate thread
    timer_thread = threading.Thread(target=run_pomodoro_timer, args=(username, user_id, users_ref, context, duration))
    timer_thread.start()


# Handle Pomodoro duration selection
def handle_pomodoro_selection(update: Update, context: CallbackContext):
    try:
        logger.debug("handle_pomodoro_selection called")  # Debug print
        query = update.callback_query
        duration_mapping = {
            'pomodoro_5': 1 * 20,
            'pomodoro_15': 15 * 60,
            'pomodoro_25': 25 * 60,
            'start_sprint': 1 * 60 * 55  # 1 hour 55 minutes
        }
        
        duration = duration_mapping.get(query.data)
        logger.debug(f"Selected duration: {duration} seconds")  # Debug print
        if duration:
            pomodoro_timer(update, context, duration)
    except Exception as e:
        logger.error(f"Error in handle_pomodoro_selection: {e}")


def simple_timer(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username
    user_id = user.id

    if not is_user_in_group(user_id, context):
        update.callback_query.edit_message_text("You must be a member of at least one group to use this service.")
        show_groups(update.callback_query)
        return

    users_ref = db.collection('users').document(username)
    users_ref.set({'username': username, 'is_active': True, 'timer_type': 'simple', 'start_time': time.time()}, merge=True)
    
    keyboard = [
        [InlineKeyboardButton("Stop Timer", callback_data='cancel_timer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=user_id, text=f"Stop Watch started for {username}. You will be notified when the timer ends.", reply_markup=reply_markup)
    get_active_user_count(update, context)

    # Start the timer in a separate thread
    timer_thread = threading.Thread(target=run_simple_timer, args=(username, user_id, users_ref, context))
    timer_thread.start()

# Run Pomodoro timer in a separate thread
def run_pomodoro_timer(username, user_id, users_ref, context, duration):
    time.sleep(duration)  # Duration from user selection

    user_data = users_ref.get().to_dict()
    if user_data and user_data.get('is_active'):
        users_ref.update({'is_active': False})
        log_timer_session(username, duration)
        send_notification(context, user_id, "⏰ Your Pomodoro Session is Up! Time to Take a Break! ☕️")

# Run Simple timer in a separate thread
def run_simple_timer(username, user_id, users_ref, context):
    time.sleep(240 * 60)  # 4 hours
    users_ref.update({'is_active': False})
    send_notification(context, user_id, "Stop Watch session has ended.")

# Function to send a notification to the user
def send_notification(context, user_id, message):
    context.bot.send_message(chat_id=user_id, text=message)

# Get the active user count
def get_active_user_count(update: Update, context: CallbackContext):
    logger.info("get_active_user_count called")
    users_ref = db.collection('users').where('is_active', '==', True)
    active_users = len(users_ref.get())
    logger.info(f"Active users: {active_users}")

    if update.callback_query:
        context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=f"📚 Active Learners Right Now: {active_users}")
    else:
        update.message.reply_text(f"📚 Active Learners Right Now: {active_users}")

# Stop the timer
def stop_timer(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username

    users_ref = db.collection('users').document(username)
    users_ref.update({'is_active': False})

    update.message.reply_text(f"Timer stopped for {username}.")

def handle_cancel(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username

    # Get the user's document reference
    users_ref = db.collection('users').document(username)
    user_data = users_ref.get().to_dict()

    if user_data and user_data.get('is_active'):
        # Calculate elapsed time
        start_time = user_data.get('start_time')
        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)

        # Log the session
        log_timer_session(username, elapsed_time)

        # Stop the timer
        users_ref.update({'is_active': False, 'start_time': None})

        # Notify the user
        context.bot.send_message(
            chat_id=user.id,
            text=f"🛑 Timer Stopped! You Studied for {elapsed_minutes} minutes and {elapsed_seconds} seconds."
        )
    else:
        context.bot.send_message(chat_id=user.id, text=f"No active timer found for {username}.")


# Modify the stop function to log the session
def log_timer_session(username, duration_seconds):
    # Reference to the user's timer sessions
    sessions_ref = db.collection('users').document(username).collection('timer_sessions')
    
    # Add a new session document
    sessions_ref.add({
        'duration': duration_seconds,  # Duration in seconds
        'timestamp': firestore.SERVER_TIMESTAMP  # Log the current time
    })
    
# Get the total time spent on the timer in the last 'days' days
import datetime

def get_total_time(username, days):
    # Get the current time and the time 'days' ago
    now = time.time()
    start_time = now - days * 24 * 60 * 60
    logger.debug(f"Current time: {now}")
    logger.debug(f"Start time (days ago): {start_time}")

    # Reference to the user's timer sessions collection
    sessions_ref = db.collection('users').document(username).collection('timer_sessions')
    
    # Query to get all sessions
    sessions = sessions_ref.stream()

    # Calculate the total duration
    total_seconds = 0
    for session in sessions:
        session_data = session.to_dict()
        session_timestamp = session_data.get('timestamp')

        # Convert datetime to Unix timestamp
        if isinstance(session_timestamp, datetime.datetime):
            session_timestamp = session_timestamp.timestamp()

        # Check if the session's timestamp is within the last 'days'
        if session_timestamp >= start_time:
            duration = session_data.get('duration', 0)
            total_seconds += duration

    logger.info(f"Total time for {username} in the last {days} days: {total_seconds} seconds")
    return total_seconds




# Show the user's timer usage stats
def show_stats(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username

    # Get total time for 1 day and 7 days
    total_time_day = get_total_time(username, 1)
    total_time_week = get_total_time(username, 7)

    # Convert the total time from seconds to hours, minutes, and seconds
    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours} hours, {minutes} minutes, {seconds} seconds"

    day_time_formatted = format_time(total_time_day)
    week_time_formatted = format_time(total_time_week)

    # Send the stats to the user
    context.bot.send_message(
        chat_id=update.callback_query.message.chat_id,
        text=(
            f"📝 You’ve Dedicated:\n\n"
            f"Today: {day_time_formatted}\n"
            f"Last 7 days: {week_time_formatted}"
        )
    )
 
 # Show the leaderboard   
def show_leaderboard(update: Update, context: CallbackContext):
    try:
        logger.debug("Calculating daily leaderboard")
        users_ref = db.collection('users')
        users = users_ref.stream()

        # Get the start and end timestamps for the current day
        now = time.time()
        start_of_day = now - (now % (24 * 60 * 60))  # Midnight of the current day

        user_times = []
        for user in users:
            username = user.id
            # Get total time for today only
            total_time = get_total_time(username, 1)  # Pass 1 to indicate 1 day

            # Only include users who have logged time today
            if total_time > 0:
                user_times.append((username, total_time))

        # Sort the users based on total time in descending order and get the top 3
        top_users = sorted(user_times, key=lambda x: x[1], reverse=True)[:3]

        # Helper function to format time
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            if hours > 0:
                return f"{hours} hours and {minutes} minutes"
            elif minutes > 0:
                return f"{minutes} minutes"
            else:
                return f"{seconds} seconds"

        # Format the leaderboard message
        leaderboard_message = "🏆 Leaderboard:\n\n"
        medals = ["🥇", "🥈", "🥉"]
        if top_users:
            for i, (username, total_time) in enumerate(top_users, start=1):
                formatted_time = format_time(total_time)
                medal = medals[i - 1] if i <= 3 else ""
                leaderboard_message += f"{medal} <b>{username}</b>: {formatted_time}\n"
            leaderboard_message += "\nChampions defend, challengers rise ⚡️"
        else:
            leaderboard_message += "No users have logged time today."

        # Check whether it's a callback query or a command
        if update.callback_query:
            update.callback_query.message.reply_text(leaderboard_message, parse_mode=telegram.ParseMode.HTML)
        else:
            update.message.reply_text(leaderboard_message, parse_mode=telegram.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error showing leaderboard: {e}")
        if update.callback_query:
            update.callback_query.message.reply_text("Unable to display the leaderboard. Please try again later.")
        else:
            update.message.reply_text("Unable to display the leaderboard. Please try again later.")




def main():
    updater = Updater('7556914561:AAHMoS1FEWJDOEAxXBO0-qrMWleaeJU8aGw', use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("active_users", get_active_user_count))
    dispatcher.add_handler(CommandHandler("stop", stop_timer))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("services", show_services))  # Link /services to show_services function
    dispatcher.add_handler(CommandHandler("show_leaderboard", show_leaderboard))
    dispatcher.add_handler(CallbackQueryHandler(handle_pomodoro_selection, pattern='^(pomodoro_5|pomodoro_15|pomodoro_25|start_sprint)$'))
    dispatcher.add_handler(CallbackQueryHandler(handle_cancel, pattern='^cancel_timer$'))
    dispatcher.add_handler(CallbackQueryHandler(show_stats, pattern='^pomodoro_stats$'))
    
    # Set bot commands
    set_bot_commands(updater)



    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
