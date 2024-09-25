import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import qrcode
from io import BytesIO

TOKEN = '7631998612:AAGoMRa198PmHs81qf9x6DBGL6_YtsWQ0Do'

# Conversation states
CHOOSING, COLOR_INPUT = range(2)

# Default colors and fixed version
DEFAULT_FILL = "black"
DEFAULT_BACK = "white"
QR_VERSION = 2  # Fixed version for all QR codes

# Store user preferences
user_preferences = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_preferences:
        user_preferences[user_id] = {'fill': DEFAULT_FILL, 'back': DEFAULT_BACK}
    
    await update.message.reply_text(
        'Welcome! Send me any text or link, and I\'ll generate a QR code for you.\n'
        'Use /colors to change QR code colors.'
    )

async def colors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Fill Color", callback_data='fill'),
         InlineKeyboardButton("Background Color", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose which color to change:', reply_markup=reply_markup)
    return CHOOSING

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['color_choice'] = query.data
    await query.message.reply_text(f"Send me the new {query.data} color (e.g., red, #FF0000):")
    return COLOR_INPUT

async def set_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    color = update.message.text.lower()
    color_type = context.user_data.get('color_choice')

    if color_type:
        user_preferences[user_id][color_type] = color
        await update.message.reply_text(
            f"{color_type.capitalize()} color set to: {color}\n"
            "You can now send me any text or link to generate a QR code, or use /colors to change colors again."
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Something went wrong. Please use /colors to start over.")
        return ConversationHandler.END

async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_preferences:
        user_preferences[user_id] = {'fill': DEFAULT_FILL, 'back': DEFAULT_BACK}

    text = update.message.text
    prefs = user_preferences[user_id]

    qr = qrcode.QRCode(version=QR_VERSION, box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=prefs['fill'], back_color=prefs['back'])
    
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    await update.message.reply_photo(photo=bio, caption="Here's your QR code!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Color change cancelled. You can send me text or a link to generate a QR code.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("colors", colors)],
        states={
            CHOOSING: [CallbackQueryHandler(button)],
            COLOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_color)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_qr))

    application.run_polling()

if __name__ == '__main__':
    main()