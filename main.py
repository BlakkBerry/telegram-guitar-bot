from config import BOT_TOKEN
from config import load_logger
from logging import getLogger
from db import init_db
from db import get_chords_names
from db import get_chord_versions
from db import get_user_instrument
from db import set_default_instrument

from telegram import Update
from telegram.ext import Updater
from telegram.ext import Filters
from telegram import KeyboardButton
from telegram import InputMediaPhoto
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import CallbackContext
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext import CallbackQueryHandler

load_logger()

logger = getLogger(__name__)

GUITAR_CALLBACK = 'guitar'
UKULELE_CALLBACK = 'ukulele'

DEFAULT_GUITAR_CALLBACK = 'default_guitar'
DEFAULT_UKULELE_CALLBACK = 'default_ukulele'

NEXT_CALLBACK = "next"
PREVIOUS_CALLBACK = "previous"

C, Csharp, Db, D, Eb, E, F, Fsharp, Gb, G, Ab, A, Bb, B = \
    'C', 'C#', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'

GUITAR_NOTE_LIST = [C, Csharp, D, Eb, E, F, Fsharp, G, Ab, A, Bb, B]

UKULELE_NOTE_LIST = [C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B]

TYPE, NOTE, DEFAULT = range(3)


def debug_requests(f):
    def inner(*args, **kwargs):
        try:
            logger.debug(f"Call function {f.__name__}")
            return f(*args, **kwargs)
        except Exception:
            logger.exception(f"Exception inside {f.__name__}")
            raise

    return inner


@debug_requests
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Choose your instrument",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Guitar', callback_data=GUITAR_CALLBACK),
                    InlineKeyboardButton(text='Ukulele', callback_data=UKULELE_CALLBACK),
                ]
            ],
        )
    )
    return TYPE


@debug_requests
def type_callback_handler(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    callback_data = callback_query.data

    if callback_data == GUITAR_CALLBACK:
        instrument = "guitar"
        callback_query.edit_message_text(
            text="Choose a note",
            reply_markup=get_note_keyboard(instrument)
        )
    elif callback_data == UKULELE_CALLBACK:
        instrument = "ukulele"
        callback_query.edit_message_text(
            text="Choose a note",
            reply_markup=get_note_keyboard(instrument)
        )
    else:
        return ConversationHandler.END

    context.user_data[TYPE] = instrument

    return NOTE


@debug_requests
def get_note_keyboard(_type: str):
    if _type.lower().strip() == "guitar":
        inline_keyboard = [
            [InlineKeyboardButton(text='C', callback_data='C'), InlineKeyboardButton(text='C#', callback_data='C#'),
             InlineKeyboardButton(text='D', callback_data='D'), InlineKeyboardButton(text='Eb', callback_data='Eb')],
            [InlineKeyboardButton(text='E', callback_data='E'), InlineKeyboardButton(text='F', callback_data='F'),
             InlineKeyboardButton(text='F#', callback_data='F#'), InlineKeyboardButton(text='G', callback_data='G')],
            [InlineKeyboardButton(text='Ab', callback_data='Ab'), InlineKeyboardButton(text='A', callback_data='A'),
             InlineKeyboardButton(text='Bb', callback_data='Bb'), InlineKeyboardButton(text='B', callback_data='B')]]
    elif _type.lower().strip() == "ukulele":
        inline_keyboard = [
            [InlineKeyboardButton(text='C', callback_data='C'), InlineKeyboardButton(text='Db', callback_data='Db'),
             InlineKeyboardButton(text='D', callback_data='D'), InlineKeyboardButton(text='Eb', callback_data='Eb')],
            [InlineKeyboardButton(text='E', callback_data='E'), InlineKeyboardButton(text='F', callback_data='F'),
             InlineKeyboardButton(text='Gb', callback_data='Gb'), InlineKeyboardButton(text='G', callback_data='G')],
            [InlineKeyboardButton(text='Ab', callback_data='Ab'), InlineKeyboardButton(text='A', callback_data='A'),
             InlineKeyboardButton(text='Bb', callback_data='Bb'), InlineKeyboardButton(text='B', callback_data='B')]]
    else:
        return None

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


@debug_requests
def note_callback_handler(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    callback_data = callback_query.data

    context.user_data[NOTE] = callback_data

    chords = get_chords_names(context.user_data[TYPE], context.user_data[NOTE])

    keyboard = []
    row = []

    counter = 0
    every = 4

    for chord in chords:
        row.append(KeyboardButton(text=chord))
        counter += 1
        if counter == every:
            keyboard.append(row)
            row = []
            counter = 0
    if row:
        keyboard.append(row)

    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

    callback_query.edit_message_text(
        text="Choose a note",
    )

    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text="Choose a chord",
        reply_markup=reply_markup,
    )

    return ConversationHandler.END


@debug_requests
def find_chord_handler(update: Update, context: CallbackContext):
    if TYPE not in dict(context.user_data).keys():
        instrument = get_user_instrument(update.effective_user.id)
        if instrument:
            context.user_data[TYPE] = instrument
        else:
            context.user_data[TYPE] = "guitar"

    chords, name = get_chord_versions(context.user_data[TYPE], update.message.text)

    if not chords:
        exception = f'{update.effective_user.first_name} {update.effective_user.last_name} AKA {update.effective_user.username} дурачєла вводить всяку фігню. А саме "{update.message.text}"'

        context.bot.send_message(chat_id=465739970,
                                 text=exception)
        logger.info(exception)

        context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text="Sorry, I don't know this chord",
                                 reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.bot.send_message(chat_id=update.effective_message.chat_id,
                             reply_markup=ReplyKeyboardRemove(),
                             text=f'Found {len(chords)} fingerings of "{update.message.text}"')

    context.bot.send_media_group(
        chat_id=update.effective_message.chat_id,
        media=[InputMediaPhoto(media=open(chord, "rb")) for chord in chords]
    )

    context.user_data.clear()

    return ConversationHandler.END


@debug_requests
def set_default_handler(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Choose your instrument",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Guitar', callback_data=DEFAULT_GUITAR_CALLBACK),
                    InlineKeyboardButton(text='Ukulele', callback_data=DEFAULT_UKULELE_CALLBACK),
                ]
            ],
        )
    )
    return DEFAULT


@debug_requests
def set_default_db_handler(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    callback_data = callback_query.data

    if callback_data == DEFAULT_GUITAR_CALLBACK:
        set_default_instrument(update.effective_user.id, "guitar")
    elif callback_data == DEFAULT_UKULELE_CALLBACK:
        set_default_instrument(update.effective_user.id, "ukulele")

    callback_query.edit_message_text(
        text=f"Default instrument was set as {callback_data.replace('default_', '')}!"
    )

    return ConversationHandler.END


@debug_requests
def cancel_handler(update: Update, context: CallbackContext):
    context.user_data.clear()
    context.bot.send_message(chat_id=update.effective_message.chat_id,
                             text="You've cancelled the chord constructor\n"
                                  "Type /start to run it or just type your cord it the chat",
                             reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


@debug_requests
def main():
    logger.info('Start GuitarBot')

    updater = Updater(
        use_context=True,
        token=BOT_TOKEN,
    )

    # Initialize the database
    init_db()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],
        states={
            TYPE: [
                CallbackQueryHandler(type_callback_handler, pass_user_data=True)
            ],
            NOTE: [
                CallbackQueryHandler(note_callback_handler, pass_user_data=True)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler, pass_user_data=True)
        ],
    )

    default_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("default", set_default_handler)
        ],
        states={
            DEFAULT: [
                CallbackQueryHandler(set_default_db_handler)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler, pass_user_data=True)
        ]
    )
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, find_chord_handler, pass_user_data=True))
    updater.dispatcher.add_handler(default_conv_handler)

    updater.start_polling()
    updater.idle()
    logger.info("Stop GuitarBot")


if __name__ == '__main__':
    main()
