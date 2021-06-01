from config import API_TOKEN, DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER, admin_id
from db_module import DB_module
import datetime 
# Data base
DB = DB_module(DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT)

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
    
    
text_1 = ['КАША','ЩИ','ПЮРЕ']

text_2 = ['ОМЛЕТ','БОРЩ','ПАСТА']

text_3 = ['ОЛАДЬИ','ЛАПША','ШАШЛЫК']

list_text = [text_1, text_2, text_3]

date = datetime.date.today()

for i in range(150):
    for text in list_text:
        date += datetime.timedelta(days=1)
        menu_id = DB.add_menu(date=date)    
        for name in text:
            DB.add_dish(menu_id, name)
    
    

