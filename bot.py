import asyncio
import logging
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import callback_data, exceptions

from config import API_TOKEN, DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, admin_id
from db_module import DB_module
from poll_module import get_text_from, get_next_question 
from analysis_module import get_analysis


# Data base
DB = DB_module(DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT)


# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('messages_sender')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# sructure of callback bottons 
button_cb = callback_data.CallbackData('button', 'question_name', 'answer', 'data')


like_word = 'Нравится'
like_mark = 2
dislike_word = 'Не нравится'
dislike_mark = 1
like_dislike_list = ['Нравится', 'Не нравится']
like_list = ['Нравится 👍', 'Не нравится']
dislike_list = ['Нравится', 'Не нравится 👎']

keywords_day =  ['Меню позавчера', 
                 'Меню вчера', 
                 'Меню сегодня']
loyaltyMark_word = 'Оценить работу компании' 
basemenu_list = keywords_day + [loyaltyMark_word,]

who_should_send_menu = {}



def make_keyboard(question_name, answers, data = 0):
    """ Возвращает клавиатуру """
    if not answers: return None

    keyboard = types.InlineKeyboardMarkup()
    row = []
    for answer in answers: # make a botton for every answer 
        cb_data=button_cb.new(question_name = question_name,
                              answer = answer,
                              data = data)
        row.append(types.InlineKeyboardButton(answer,
                                              callback_data=cb_data))
    if len(row) <= 2: keyboard.row(*row)
    elif len(row) == 10:
        keyboard.row(*row[:5])
        keyboard.row(*row[5:])
    else:
        for button in row: keyboard.row(button)
        
    return keyboard


def get_basemenu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in basemenu_list: keyboard.add(types.KeyboardButton(name))
    return keyboard
    
def check_low_answers(user_id):
    answer = DB.get_last_answer(user_id = user_id)
    for name in ['loyalty', 'manager', 'delivery', 'cooking', 'dietetics']:
        if int(answer[name]) < 7: return True
    return False


@dp.message_handler(commands=['start'])
async def send_phone(message: types.Message):
    logging.info('start command from: %r', message.from_user.id) 
    
    DB.add_user(message.from_user.id, 
                message.from_user.first_name, 
                message.from_user.last_name, 
                message.from_user.username, 
                message.from_user.language_code)

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, 
                                         resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Отправить телефон 📞', 
                                      request_contact=True))
    text = get_text_from('./text_of_questions/authorization.txt')
    await message.answer(text, reply_markup = keyboard)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    logging.info('help command from: %r', message.from_user.id) 
    keyboard = get_basemenu_keyboard()
    await message.answer(get_text_from('./text_of_questions/help.txt'), 
                         reply_markup=keyboard)


@dp.callback_query_handler(button_cb.filter(
    question_name=['start', 'loyalty', 'manager', 'delivery', 'cooking', 'dietetics']))
async def callback_vote_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    
    # callback_data contains all info from callback data
    logging.info('Got this callback data: %r', callback_data) 
    
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_question = callback_data['question_name']
    callback_answer = callback_data['answer']
    
    DB.add_answer(user_id = query.from_user.id, 
                  question_name = callback_question, 
                  answer = callback_answer)
    
    question_name, text, answers = get_next_question(callback_question,
                                                     callback_answer)
    keyboard = make_keyboard(question_name, answers)
    
    edited_text = query.message.text + '\n\nВаша оценка: ' + callback_answer

    await bot.edit_message_text(
        edited_text,
        query.from_user.id,
        query.message.message_id,
        reply_markup=None,
        )
    
    await bot.send_message(query.from_user.id, text, reply_markup = keyboard)
    
    if question_name == 'end':
        if check_low_answers(query.from_user.id):
            await bot.send_message( 
                query.from_user.id, 
                'Расскажите, почему вы поставили низкую оценку?')
        else:
            await bot.send_message( 
                query.from_user.id, 
                'Вы так-же можете оставить тут свой отзыв.')


    
async def send_menu(user_id, keyword_day):
    """ 
    Клиент выбрал день. 
    Бот отправляет меню - список блюд с лайками/дизлайками
    
    """
    menu = DB.get_menu(keyword=keyword_day)
    if not menu:
        await bot.send_message(user_id, 'Извините, меню на этот день отсутствует')
        return
    
    dishes = DB.get_dish(menu_id=menu['id'])
    
    await bot.send_message(user_id, '📅 Меню на '+str(menu['date'])+':')
    
    for dish in dishes:
        feedback = DB.get_feedback(user_id = user_id, dish_id = dish['id'])
        if not feedback:
            list_for_keybord = like_dislike_list
        elif feedback['mark'] == 2:
            list_for_keybord = like_list
        elif feedback['mark'] == 1:
            list_for_keybord = dislike_list
        else:
            list_for_keybord = like_dislike_list
            
        keyboard = make_keyboard('feedback', 
                                 list_for_keybord, 
                                 dish['id'])
        await bot.send_message(user_id, dish['name'], reply_markup = keyboard)
    
    
@dp.callback_query_handler(button_cb.filter(question_name=['feedback']))
async def callback_like(query: types.CallbackQuery, 
                               callback_data: typing.Dict[str, str]):
    """ Клиент поставил лайк под блюдом. """
    # callback_data contains all info from callback data
    logging.info('Got this callback data: %r', callback_data) 
    
    await query.answer()  # don't forget to answer callback query as soon as possible
    from_user = query.from_user.id
    callback_question = callback_data['question_name']
    callback_answer = callback_data['answer']
    callback_ans_data = callback_data['data']
    
    if not callback_answer in like_dislike_list: return
    
    if callback_answer == like_word:
        mark_from_user = like_mark
        list_for_keyboard = like_list
    elif callback_answer == dislike_word:
        mark_from_user = dislike_mark
        list_for_keyboard = dislike_list 
    
    DB.update_feedback(user_id = from_user, 
                       dish_id = callback_ans_data, 
                       mark = mark_from_user)    
    
    keyboard = make_keyboard(callback_question, 
                             list_for_keyboard, 
                             callback_ans_data )

    await bot.edit_message_text(query.message.text,
                                query.from_user.id,
                                query.message.message_id,
                                reply_markup=keyboard )
    

@dp.message_handler(commands=['admin'])
async def admin_options(message: types.Message):
    logging.info('admin command from: %r', message.from_user.id) 
    
    if message.from_user.id in admin_id:
        question_name, text, answers = get_next_question('admin_options')
        keyboard = make_keyboard(question_name, answers)
    else: 
        text = 'У вас нет доступа'
        keyboard = None
        
    await message.answer(text, reply_markup = keyboard)


@dp.callback_query_handler(button_cb.filter(question_name=['admin']))
async def callback_admin_action(
    query: types.CallbackQuery, callback_data: typing.Dict[str, str]):
    
    # callback_data contains all info from callback data
    logging.info('Got this callback data: %r', callback_data) 
    
    await query.answer()  # don't forget to answer callback query as soon as possible
    callback_question = callback_data['question_name']
    callback_answer = callback_data['answer']
    
    question_name, text, answers = get_next_question(callback_question,
                                                     callback_answer)
    keyboard = make_keyboard(question_name, answers)
    
    await bot.send_message(query.from_user.id, text, reply_markup = keyboard)
    
    if question_name == 'table_loyalty':
        headings = ['id', 'Имя','Фамилия','username','язык','номер телефона',
                    'id','id', 'дата ответа', 'лояльность', 'менеджер', 
                    'доставка', 'кулинария', 'диетология', 'отзыв']
        filepath = 'smartfood_all_answers.xls'
        DB.export_answer_loyalty_to_excel(headings, filepath)
        document = open(filepath,'rb')
        await bot.send_document(query.from_user.id, document)
        
    elif question_name == 'analysis':
        text = get_analysis(DB.get_answers())
        await bot.send_message(query.from_user.id, text)
    
    elif question_name == 'table_menu_fb':
        headings =['Имя', 'Фамилия', 'username', 'номер телефон', 
                   'название блюда', 'дата меню', 'дата отзыва', 
                   'отметка (2-нравится, 1-не нравится)', 'отзыв'] 
        filepath = 'smartfood_menu_feedback.xls'
        DB.export_menu_feedback_to_excel(headings, filepath)
        document = open(filepath,'rb')
        await bot.send_document(query.from_user.id, document)
        
    elif question_name == 'add_new_menu':
        who_should_send_menu[query.from_user.id] = True
    
        text = get_text_from('./text_of_questions/menu_exemple.txt')
        await bot.send_message(query.from_user.id, text)
        
    elif question_name == 'stop_add':
        who_should_send_menu[query.from_user.id] = False
        

        
    
    
@dp.message_handler(lambda message: message.text in basemenu_list)
async def base_menu(message: types.Message):
    """
    Получаем нажатие кнопки из базового меню
    Запускаем соответствующие процесс:
        Оценка меню
        Оценка компании
    """
    logging.info('push basemenu button from: %r', message.from_user.id)
    if message.text in keywords_day:
        await message.answer(get_text_from('./text_of_questions/menu_instruction.txt'))
        await send_menu(message.from_user.id, message.text)
    elif message.text == loyaltyMark_word:
        await message.answer(get_text_from('./text_of_questions/start_poll.txt'))
        question_name, text, answers = get_next_question('start_poll')
        keyboard = make_keyboard(question_name, answers)
        await message.answer(text, reply_markup = keyboard )
        
    return 

def parse_message(text):
    message_list = text.split('\n')
    try:
        menu_id = DB.add_menu(str_date = message_list[0])
        if not menu_id: 
            return 'Ошибка. Можно добавлять меню только на будущие дни'
            
        for i in range(1,len(message_list)):
            if message_list[i]!='':
                DB.add_dish(menu_id, message_list[i])
        return f'Новое меню на {message_list[0]} добавлено.'
    except:
        return 'Ошибка. Не удалось добавить это меню'


@dp.message_handler(content_types = types.message.ContentType.TEXT)
async def new_text_message(message: types.Message):
    """
    Принимает текстовые сообщения
    Если это ответет на сообщение с блюдом, то записывается отзыв на блюдо
    Иначе просто какой-то отзыв 
    """
    newmessage_is_simple_review = True
    if 'reply_to_message' in message:
        reply_to_message = message.reply_to_message
        if 'reply_markup' in reply_to_message:
            newmessage_is_simple_review = False
            inline_keyboard = reply_to_message.reply_markup.inline_keyboard
            dish_id_str = inline_keyboard[0][0].callback_data.split(':')[-1]
            DB.update_feedback(user_id = message.from_user.id, 
                               dish_id = int(dish_id_str), 
                               review = message.text) 
            logging.info('new review from: %r', message.from_user.id)
            await message.reply('Я передам ваш отзыв. Спасибо!')
    
    elif message.from_user.id in who_should_send_menu:
        if who_should_send_menu[message.from_user.id]:
            newmessage_is_simple_review = False
            text = parse_message(message.text)
            await message.reply(text)
        
    if newmessage_is_simple_review:
        logging.info('new message from: %r', message.from_user.id) 
        DB.add_review(user_id = message.from_user.id, text = message.text)
        keyboard = get_basemenu_keyboard()
        await message.reply('Я передам эту информацию руководству компании. Спасибо!',
                            reply_markup=keyboard)
    

@dp.message_handler(content_types = types.message.ContentType.CONTACT)
async def new_contact(message: types.Message):
    """
    Если приходит контакт, то записываем как новый номер юзера
    И отправляем help и базавое меню
    
    """
    logging.info('new phone from: %r', message.from_user.id) 
    DB.add_phone(user_id = message.from_user.id, 
                 phone = message.contact.phone_number)
    await message.reply(get_text_from('./text_of_questions/phone.txt'),
                        reply_markup = types.ReplyKeyboardRemove())
    
    text = get_text_from('./text_of_questions/first_instruction.txt')
    keyboard = get_basemenu_keyboard()
    await message.answer(text, reply_markup = keyboard)


@dp.message_handler(content_types = types.message.ContentType.ANY)
async def staf(message: types.Message):
    """ любой другой контент просто отметаем"""
    logging.info('strange staf from: %r', message.from_user.id)
    await message.reply(get_text_from('./text_of_questions/wtf.txt'))



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)