from flask import Flask, request
import logging
import json
# импортируем функции из нашего второго файла geo
from geo import get_country, get_distance, get_coordinates, get_capitalcity
from flask_ngrok import run_with_ngrok

app = Flask(__name__)
run_with_ngrok(app)
# Добавляем логирование в файл.
# Чтобы найти файл, перейдите на pythonwhere в раздел files,
# он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = \
            """Привет! Я простой Городовед. Я могу:
                - Найти столицу страны;
                - Определить страну по городу;
                - Найти расстояние между двумя городами России.
               Что хотите найти?"""
        sessionStorage[user_id] = {
            'action': None
        }
        return
    if sessionStorage[user_id]['action'] is None:
        # res['response']['text'] = 'Что ищем?'
        action = get_action(req)
        if action is None:
            res['response']['text'] = "Что-то непонятное. Повтори запрос."
        elif action == "Стоп":
            res['response']['text'] = "Пока!"
            res['response']['end_session'] = True
            return
        elif action == "Помощь":
            res['response']['text'] = """
                Для начала выберете, что хотите найти.
                
                Чтобы узнать столицу страны, введите название одной страны.
                Чтобы узнать страну, в которой находится город, введите название одного города.
                Чтобы узнать расстояние между двумя городами России, введите названия двух городов России.
                Чтобы прекратить работу навыка введите 'Стоп', 'Выход' и т.п.
                
                Итак, что ищем?"""
        elif action == "Найти столицу страны":
            res['response']['text'] = "Введите название страны"
            sessionStorage[user_id]['action'] = action
        elif action == "Найти расстояние между двумя городами России":
            res['response']['text'] = "Введите названия двух Российских городов"
            sessionStorage[user_id]['action'] = action
        elif action == "Определить страну по городу":
            res['response']['text'] = "Введите название города"
            sessionStorage[user_id]['action'] = action

    elif sessionStorage[user_id]['action'] == "Найти столицу страны":
        countryes = get_countryes(req)
        if not countryes:
            res['response']['text'] = 'Ты не написал название не одной страны!'
        elif len(countryes) == 1:
            res['response']['text'] = f"""Столица этой страны - {get_capitalcity(countryes[0])}
                                          Что ещё хотите найти?"""
            sessionStorage[user_id]['action'] = None
        else:
            res['response']['text'] = 'Слишком много стран!'
    elif sessionStorage[user_id]['action'] == "Найти расстояние между двумя городами России":
        cities = get_cities(req)
        if not cities:
            res['response']['text'] = 'Ты не написал название не одного города!'
        elif len(cities) == 1:
            res['response']['text'] = 'Ты написал только 1 город России'
        elif len(cities) == 2:
            distance = get_distance(get_coordinates(
                cities[0]), get_coordinates(cities[1]))
            res['response']['text'] = f"""Расстояние между этими городами: {str(round(distance))} км.
                                          Что ещё хотите найти?"""
            sessionStorage[user_id]['action'] = None
        else:
            res['response']['text'] = 'Слишком много городов!'
    elif sessionStorage[user_id]['action'] == "Определить страну по городу":
        cities = get_cities(req)
        if not cities:
            res['response']['text'] = 'Ты не написал название не одного города!'
        elif len(cities) == 1:
            res['response']['text'] = f"""Этот город в стране - {get_country(cities[0])}
                                          Что ещё хотите найти?"""
            sessionStorage[user_id]['action'] = None
        else:
            res['response']['text'] = 'Слишком много городов!'


def get_action(req):
    command = req['request']['nlu']['tokens']
    for com in command:
        com = com.lower()
        if com in ["столица",
                   "столицу"]:
            return "Найти столицу страны"

        elif com in ['расстояние']:
            return "Найти расстояние между двумя городами России"

        elif com in ['страна',
                     'страну',
                     'стране']:
            return "Определить страну по городу"

        elif com in ['помощь',
                     'справка',
                     'помоги',
                     'подскажи',
                     'инструкция']:
            return "Помощь"

        elif com in ['стоп',
                     'конец',
                     'завершить',
                     'прекратить',
                     'пока',
                     'досвидание',
                     'выход']:
            return "Стоп"
    return


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


def get_countryes(req):
    countryes = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'country' in entity['value']:
                countryes.append(entity['value']['country'])
    return countryes


if __name__ == '__main__':
    app.run()