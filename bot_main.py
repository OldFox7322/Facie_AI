import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
import requests
import logging
import os 

# Load environment variables from .env
load_dotenv()

# Load tokens and API URLs from environment
BOT_TOKEN = os.getenv('BOT_TOKEN') 
FASTAPI_URL = os.getenv('FASTAPI_URL') 
BOT_ID = BOT_TOKEN.split(":")[0]

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Temporary in-memory user data storage
user_data = {}

# Conversation states
CHOOSING_ACTION = 0
AWAITING_NAME = 1
AWAITING_PROFESSION = 2
AWAITING_DESCRIPTION = 3
AWAITING_PHOTO = 4
FINISHING = 5
AWAITING_FRIEND_ID = 6
AWAITING_AI_QUESTION = 7


# Entry point — /start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)


# Creates the inline keyboard for the main menu
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(" Додати нового друга (POST)", callback_data='start_post')],
        [InlineKeyboardButton("Показати всіх друзів (GET)", callback_data='show_all_friends')],
        [InlineKeyboardButton("Знайти друга за ID (GET)", callback_data='get_friend_by_id')],
        [InlineKeyboardButton("Видалити друга за ID (DELETE)", callback_data='delete_friend')],
        [InlineKeyboardButton("Запитати про професію (AI)", callback_data='ask_ai')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Displays the main menu (can be triggered by /start or button navigation)
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    reply_markup = get_main_menu_keyboard() 

    if update.callback_query:
        # Update the existing message if triggered by callback
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Оберіть, яку дію ви хочете виконати з бекендом:",
            reply_markup=reply_markup
        )
    else:
        # Send a new message if triggered by /start
        await update.message.reply_text(
            "Оберіть, яку дію ви хочете виконати з бекендом:",
            reply_markup=reply_markup
        )

    context.user_data['state'] = CHOOSING_ACTION


# Handles all button clicks from the main menu
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id    
    await query.answer()
    
    # Start adding a new friend
    if data == 'start_post':
        user_data[user_id] = {}
        context.user_data['state'] = AWAITING_NAME
        await query.edit_message_text("Початок додавання друга. Введіть ім'я (Name):")

    # Show all friends
    elif query.data == 'show_all_friends':
        await show_all_friends(update, context)

    # Search for a friend by ID
    elif data == 'get_friend_by_id':
        context.user_data['state'] = AWAITING_FRIEND_ID
        await query.edit_message_text("Введіть, будь ласка, <b>FriendID</b> друга, якого ви хочете знайти:",
                                      parse_mode=telegram.constants.ParseMode.HTML)

    # Delete a friend by ID
    elif data == 'delete_friend':
        context.user_data['next_action'] = 'delete_friend_action'  # Flag for delete mode
        context.user_data['state'] = AWAITING_FRIEND_ID
        await query.edit_message_text(
            "Щоб видалити друга, введіть <b>FriendID</b>:",
            parse_mode=telegram.constants.ParseMode.HTML
        )

    # Ask AI about a friend’s profession
    elif data == 'ask_ai':
        context.user_data['next_action'] = 'ask_ai_question' 
        context.user_data['state'] = AWAITING_FRIEND_ID 
        await query.edit_message_text(
            "Щоб поставити запитання, спершу введіть <b>FriendID</b> друга:",
            parse_mode=telegram.constants.ParseMode.HTML
        )


# Handles user text messages and route them depending on current state
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # Step 1 — get name
    if state == AWAITING_NAME:
        user_data[user_id]['name'] = update.message.text
        context.user_data['state'] = AWAITING_PROFESSION
        await update.message.reply_text("Добре. Тепер введіть професію (Profession):")
    
    # Step 2 — get profession
    elif state == AWAITING_PROFESSION:
        user_data[user_id]['profession'] = update.message.text
        context.user_data['state'] = AWAITING_DESCRIPTION
        await update.message.reply_text("Чудово. Введіть короткий опис професії (Profession Description):")

    # Step 3 — get profession description
    elif state == AWAITING_DESCRIPTION:
        user_data[user_id]['profession_description'] = update.message.text
        context.user_data['state'] = AWAITING_PHOTO
        await update.message.reply_text("Завершальний крок: Надішліть фотографію друга (стиснене або як документ):")

    # Step 4 — get photo and send to FastAPI
    elif state == AWAITING_PHOTO:
        await process_photo(update, context)

    # Handle Friend ID inputs for GET/DELETE/AI
    elif state == AWAITING_FRIEND_ID:
        friend_id = update.message.text.strip()
        next_action = context.user_data.pop('next_action', 'get_friend_details') 
        
        if next_action == 'ask_ai_question':
            context.user_data['ai_friend_id'] = friend_id
            context.user_data['state'] = AWAITING_AI_QUESTION
            await update.message.reply_text(f"ID <code>{friend_id}</code> прийнято. Тепер введіть ваше запитання про професію друга:",
                                            parse_mode=telegram.constants.ParseMode.HTML)

        elif next_action == 'delete_friend_action':
            await process_delete_friend(update, context, friend_id)

        else:
            await process_get_friend_by_id(update, context, friend_id)

    # Handle AI question input
    elif state == AWAITING_AI_QUESTION:
        question = update.message.text
        friend_id = context.user_data.pop('ai_friend_id', None) 
        
        if friend_id:
            await process_ai_question(update, context, friend_id, question)
        else:
            await update.message.reply_text("Помилка: Не знайдено ID друга для AI-запиту. Спробуйте знову.")
            context.user_data['state'] = CHOOSING_ACTION
            await main_menu(update, context)
            
    else:
        await update.message.reply_text("Будь ласка, оберіть дію за допомогою кнопок або наберіть /start.")


# Fetch and display all friends from FastAPI
async def show_all_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Запитую список всіх друзів з FastAPI...")

    try:
        response = requests.get(FASTAPI_URL)
        response.raise_for_status()
        friends_list = response.json() 
        
        # Handle empty database
        if not friends_list:
            await update.effective_message.reply_text(
                " На жаль, у базі даних немає жодного друга.",
                reply_markup=main_menu(update, context)
            )
            return

        # Format all friends into one message
        messages = []
        for i, friend in enumerate(friends_list):
            message = (
                f"<b> Друг #{i + 1}</b>\n"
                f"<b>ID:</b> <code>{friend.get('FriendID')}</code>\n"
                f"<b>Ім'я:</b> <code>{friend.get('Name')}</code>\n"
                f"<b>Професія:</b> <code>{friend.get('Profession')}</code>\n"
                f"<b>Опис:</b> <code>{friend.get('ProfessionDescription', 'N/A')}</code>\n"
                f"<b>S3Key:</b> <code>{friend.get('S3Key')}</code>\n"
                f"<b>Посилання на Фото:</b> <a href='{friend.get('PhotoUrl')}'>Показати Фото (S3)</a>"
            )
            messages.append(message)

        final_message = "<b>Список Усіх Друзів:</b>\n\n" + "\n\n— — —\n\n".join(messages)
        
        await update.effective_message.reply_text(
            final_message,
            parse_mode=telegram.constants.ParseMode.HTML,
            disable_web_page_preview=True
        )
        
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        error_message = f"Помилка з'єднання з FastAPI: {e}"
        logging.error(error_message)
        await update.effective_message.reply_text(error_message)
        
    except Exception as e:
        # Handle unexpected issues
        error_message = f"Виникла несподівана помилка під час отримання даних: {e}"
        logging.error(error_message)
        await update.effective_message.reply_text(error_message)
        

    await update.effective_message.reply_text("Що ви хочете зробити далі?", reply_markup=get_main_menu_keyboard())


# Handle sending photo and posting new friend to FastAPI
async def process_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Accept either compressed photo or image document
    if update.message.photo:
        file_to_download = update.message.photo[-1]
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        file_to_download = update.message.document
    else:
        await update.message.reply_text("Будь ласка, надішліть саме фотографію або зображення.")
        return

    await update.message.reply_text("Фото отримано. Відправляю дані на FastAPI...")
    
    try:
        # Download the image file from Telegram servers
        telegram_file = await file_to_download.get_file()
        file_url = telegram_file.file_path
        file_content_response = requests.get(file_url)
        file_content_response.raise_for_status()
        file_content = file_content_response.content
        
        data = user_data[user_id] 
        
        # Determine file type
        if update.message.document:
            mime_type = file_to_download.mime_type
        else:
            mime_type = 'image/jpeg' 
        
        file_name = f"{user_id}_{file_to_download.file_unique_id}.jpg"
        files = {
        'photo': (file_name, file_content, mime_type) 
        }

        # POST request to FastAPI
        response = requests.post(FASTAPI_URL, data=data, files=files)
        response.raise_for_status() 
        response_data = response.json()

        # Format success response
        formatted_response = (
            f"<b>Успіх! Друг доданий.</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Ім'я:</b> <code>{response_data.get('Name')}</code>\n"
            f"<b>Професія:</b> <code>{response_data.get('Profession')}</code>\n"
            f"<b>Опис:</b> <code>{response_data.get('ProfessionDescription')}</code>\n"
            f"<b>ID Друга:</b> <code>{response_data.get('FriendID')}</code>\n"
            f"<b>S3Key Друга:</b> <code>{response_data.get('S3Key')}</code>\n"
            f"<b>Посилання на Фото:</b> <a href='{response_data.get('PhotoUrl')}'>Показати Фото (S3)</a>"
        )
        
        # Clear temporary user data
        context.user_data.clear()
        del user_data[user_id]
        await update.message.reply_text(
            formatted_response,
            parse_mode=telegram.constants.ParseMode.HTML
        )

    except requests.exceptions.HTTPError as e:
        # Handle HTTP-specific errors
        try:
            error_detail = e.response.json().get('detail', 'Невідома помилка HTTP')
        except:
            error_detail = e.response.text

        await update.message.reply_text(f"Помилка HTTP під час взаємодії з FastAPI: {error_detail}")
        logging.error(f"FastAPI error: {e}")
        
    except Exception as e:
        # Handle unexpected exceptions
        await update.message.reply_text(f"Виникла несподівана помилка: {e}")
        logging.error(f"General error: {e}")

    context.user_data['state'] = CHOOSING_ACTION
    await update.effective_message.reply_text("Що ви хочете зробити далі?", reply_markup=get_main_menu_keyboard())


# Fetch a specific friend by ID
async def process_get_friend_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_id: str):
    await update.message.reply_text(f"Шукаю друга з ID: <code>{friend_id}</code>...", 
                                    parse_mode=telegram.constants.ParseMode.HTML)
    
    API_URL_WITH_ID = f"{FASTAPI_URL}/{friend_id}"

    try:
        response = requests.get(API_URL_WITH_ID)
        response.raise_for_status() 
        friend_data = response.json() 

        # Format friend details
        formatted_response = (
            f"<b>Знайдено друга!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Ім'я:</b> <code>{friend_data.get('Name')}</code>\n"
            f"<b>Професія:</b> <code>{friend_data.get('Profession')}</code>\n"
            f"<b>Опис:</b> <code>{friend_data.get('ProfessionDescription')}</code>\n"
            f"<b>ID Друга:</b> <code>{friend_data.get('FriendID')}</code>\n"
            f"<b>S3Key:</b> <code>{friend_data.get('S3Key')}</code>\n"
            f"<b>Посилання на Фото:</b> <a href='{friend_data.get('PhotoUrl')}'>Показати Фото (S3)</a>"
        )
        
        await update.message.reply_text(
            formatted_response,
            parse_mode=telegram.constants.ParseMode.HTML
        )
        
    except requests.exceptions.HTTPError as e:
        # Handle HTTP 404 or 500
        error_detail = e.response.json().get('detail', e.response.text)
        await update.message.reply_text(f"Помилка (4xx/5xx): Не вдалося знайти друга або інша помилка: {error_detail}")
        logging.error(f"FastAPI error fetching ID {friend_id}: {e}")
        
    except Exception as e:
        await update.message.reply_text(f"Виникла несподівана помилка: {e}")
        logging.error(f"General error fetching ID {friend_id}: {e}")

    context.user_data['state'] = CHOOSING_ACTION
    await update.message.reply_text("Що ви хочете зробити далі?", reply_markup=get_main_menu_keyboard())


# Delete friend by ID
async def process_delete_friend(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_id: str):
    await update.message.reply_text(f"Надсилаю запит на видалення друга з ID: <code>{friend_id}</code>...", 
                                    parse_mode=telegram.constants.ParseMode.HTML)
    
    API_URL_WITH_ID = f"{FASTAPI_URL}/delete/{friend_id}" 
    
    try:
        response = requests.delete(API_URL_WITH_ID)
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"Друг з ID <code>{friend_id}</code> та його фото було успішно видалено з бази даних та S3.",
                parse_mode=telegram.constants.ParseMode.HTML
            )
        elif response.status_code == 404:
             await update.message.reply_text(
                f"Помилка: Друг з ID <code>{friend_id}</code> не знайдений для видалення.",
                parse_mode=telegram.constants.ParseMode.HTML
            )
        else:
            error_detail = response.json().get('detail', response.text)
            await update.message.reply_text(f"Помилка видалення (HTTP {response.status_code}). Деталі: {error_detail}")
            logging.error(f"FastAPI error deleting ID {friend_id}: {error_detail}")
            
    except requests.exceptions.RequestException as e:
        error_message = f"Помилка з'єднання з FastAPI: {e}"
        logging.error(error_message)
        await update.message.reply_text(f"{error_message}")
    
    except Exception as e:
        await update.message.reply_text(f"Виникла несподівана помилка: {e}")
        logging.error(f"General error deleting ID {friend_id}: {e}")

    context.user_data['state'] = CHOOSING_ACTION
    await update.message.reply_text("Що ви хочете зробити далі?", reply_markup=get_main_menu_keyboard())


# Send a question to FastAPI → LLM for AI answer
async def process_ai_question(update: Update, context: ContextTypes.DEFAULT_TYPE, friend_id: str, question: str):
    await update.message.reply_text("Обробляю запитання за допомогою AI. Це може зайняти до 15 секунд...")
    
    API_URL = f"{FASTAPI_URL}/{friend_id}/ask"
    payload = {"question": question}

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status() 
        ai_answer = response.json() 

        formatted_response = (
            f"<b>Відповідь AI про професію друга:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{ai_answer}</b>\n"
        )
        
        await update.message.reply_text(
            formatted_response,
            parse_mode=telegram.constants.ParseMode.HTML
        )
        
    except requests.exceptions.HTTPError as e:
        # Handle backend AI-related HTTP errors
        try:
            error_detail = e.response.json().get('detail', 'Невідома помилка')
        except:
            error_detail = e.response.text
            
        await update.message.reply_text(f"Помилка під час AI-запиту: {error_detail}")
        logging.error(f"FastAPI error fetching AI for ID {friend_id}: {e}")
        
    except Exception as e:
        await update.message.reply_text(f"Виникла несподівана помилка: {e}")
        logging.error(f"General error AI processing: {e}")


    context.user_data['state'] = CHOOSING_ACTION
    await update.message.reply_text("Що ви хочете зробити далі?", reply_markup=get_main_menu_keyboard())




def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    application.add_handler(MessageHandler(
        (filters.TEXT & ~filters.COMMAND) | filters.PHOTO | filters.Document.IMAGE, 
        handle_message
    ))
    
    logging.info("Starting bot...")
    application.run_polling(poll_interval=3)



if __name__ == '__main__':
    main()
