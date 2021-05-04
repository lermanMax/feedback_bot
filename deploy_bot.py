import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT 
from psycopg2.extras import DictCursor
from psycopg2.sql import SQL, Identifier

'''
CREATE ROLE [role_name] WITH LOGIN CREATEDB PASSWORD '[password]';
sudo -i -u postgres
CREATE database menu_db

comands for create Database in postgres for this bot:
    



'''

DB_HOST = "localhost"
DB_NAME = "menu_db"
DB_USER = "bot"
DB_PASS = "bot"

TABLE_users ="""CREATE TABLE users ( 
                id BIGINT PRIMARY KEY, 
                first_name varchar(80), 
                last_name varchar(80), 
                username varchar(80), 
                language_code varchar(80), 
                phone varchar(80)
                );"""

    
TABLE_menu = """CREATE TABLE menu ( 
                id serial PRIMARY KEY, 
                date DATE
                );""" 

TABLE_dish = """CREATE TABLE dish ( 
                id serial PRIMARY KEY, 
                menu_id BIGINT references menu(id),
                name text
                );"""  
    
TABLE_feedback = """CREATE TABLE feedback ( 
                    id serial PRIMARY KEY, 
                    user_id BIGINT references users(id),
                    dish_id BIGINT references dish(id),
                    date DATE,
                    mark INT,
                    review text                
                    );""" 

TABLE_answer_loyalty="""CREATE TABLE answer_loyalty ( 
                        id serial PRIMARY KEY, 
                        user_id BIGINT references users(id),
                        answering_date DATE,
                        loyalty INT,
                        manager INT, 
                        delivery INT,
                        cooking INT,
                        dietetics INT,
                        review text                
                        );""" 


with psycopg2.connect(
    host = DB_HOST,
    database = DB_NAME,
    user = DB_USER,
    password = DB_PASS,
    ) as conn:
    
    with conn.cursor(cursor_factory=DictCursor) as cur:
                        
        cur.execute(SQL(TABLE_users))
        cur.execute(SQL(TABLE_menu))
        cur.execute(SQL(TABLE_dish))
        cur.execute(SQL(TABLE_feedback))
        cur.execute(SQL(TABLE_answer_loyalty))
