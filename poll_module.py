import datetime 

'''
Структура словаря

{имя вопроса : {ответ_1: 'следующий вопрос'}} 

'''


question_dict = {
    'choice_menu':{
        'Меню позавчера':'two_days_ago',
        'Меню вчера':'one_day_ago',
        'Меню сегодня':'today'},
    'admin_options':{
        'default': 'admin'},
    'admin':{
        'Excel отзывы о компании': 'table_loyalty',
        'Аналитика отзывов о комп.': 'analysis',
        'Excel отзывы о меню': 'table_menu_fb',
        'Добавить новое меню': 'add_new_menu',
        'Перестать добавлять меню': 'stop_add'},
    'start_poll':{
        'default': 'loyalty'},
    'loyalty':{
        '1': 'manager', '2': 'manager', 
        '3': 'manager', '4': 'manager', 
        '5': 'manager', '6': 'manager', 
        '7': 'manager', '8': 'manager', 
        '9': 'manager', '10': 'manager'},
    'manager':{
        '1': 'delivery', '2': 'delivery', 
        '3': 'delivery', '4': 'delivery', 
        '5': 'delivery', '6': 'delivery', 
        '7': 'delivery', '8': 'delivery', 
        '9': 'delivery', '10': 'delivery'},
    'delivery':{
        '1': 'cooking', '2': 'cooking', 
        '3': 'cooking', '4': 'cooking', 
        '5': 'cooking', '6': 'cooking', 
        '7': 'cooking', '8': 'cooking', 
        '9': 'cooking', '10': 'cooking'},
    'cooking':{
        '1': 'dietetics', '2': 'dietetics', 
        '3': 'dietetics', '4': 'dietetics', 
        '5': 'dietetics', '6': 'dietetics', 
        '7': 'dietetics', '8': 'dietetics', 
        '9': 'dietetics', '10': 'dietetics'},
    'dietetics':{
        '1': 'end', '2': 'end', 
        '3': 'end', '4': 'end', 
        '5': 'end', '6': 'end', 
        '7': 'end', '8': 'end', 
        '9': 'end', '10': 'end'}
    }


def get_text_from(path):
    with open(path,'r') as file:
        one_string = ''
        for line in file.readlines():
            one_string += line
    return one_string
    

def get_next_question(question_name = 'default', 
                      answer = 'default', 
                      files_dir = './text_of_questions/'):
    
    question_name = question_dict[question_name][answer]
    question_text = get_text_from(files_dir + question_name +'.txt')
    
    if question_name not in question_dict: answers = []
    else: answers = [answer for answer in question_dict[question_name]]

    return question_name, question_text, answers


def get_date(day = 'Меню сегодня'):
    today = datetime.date.today()
    one_day_ago = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)
    
    date = {'Меню позавчера': two_days_ago,
            'Меню вчера': one_day_ago,
            'Меню сегодня': datetime.date.today()}
    
    return date[day]



