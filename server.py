import datetime
import time

import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random

from data import LOGIN, PASSWORD, GROUP_TOKEN, GROUP_ID, ALBUM_ID

d = {}


def send_photo(filename, user_id):
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    server = vk.photos.getMessagesUploadServer()
    response = requests.post(server['upload_url'], files={'file': open(filename, 'rb')}).json()
    res = vk.photos.saveMessagesPhoto(server=response['server'], photo=response['photo'], hash=response['hash'])[0]
    photo = "photo" + str(res['owner_id']) + "_" + str(res['id']) + "_" + res['access_key']

    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    vk.messages.send(user_id=user_id, message=f"Это {d[user_id]['request']}.Что вы ещё хотите увидеть?",
                     random_id=random.randint(0, 2 ** 64), attachment=photo)
    print("message have been sent")


def main():
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)

    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    maps = {
        'схема': ["map", 'png'],
        'спутник': ['sat', 'jpeg'],
        'гибрид': ['sat,skl', 'jpeg']
    }
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_id = event.obj.message['from_id']
            m_took = event.obj.message['text']
            print('Новое сообщение:')
            print('Для меня от:', user_id)
            print('Текст:', m_took)
            if user_id not in d.keys():
                d[user_id] = {
                    'stage': 0
                }
            else:
                d[user_id]['stage'] += 1
                if d[user_id]['stage'] == 3:
                    d[user_id]['stage'] = 1
            vk = vk_session.get_api()
            if d[user_id]['stage'] == 0:
                vk.messages.send(user_id=user_id, message="Здравствуйте, укажите местность которую хотите увидеть.",
                                random_id = random.randint(0, 2 ** 64))
            elif d[user_id]['stage'] == 1:
                request = f"http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode" \
                    f"={m_took}&format=json"
                response = requests.get(request)
                if not response:
                    m_given = "Wrong Input"
                else:
                    json_response = response.json()
                    if len(json_response["response"]["GeoObjectCollection"][
                               "featureMember"]) == 0:
                        m_given = "Wrong Input"
                    else:
                        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                        toponym_coodrinates = toponym["Point"]["pos"]
                        longitude, latitude = toponym_coodrinates.split()
                        d[user_id]['request'] = m_took
                        d[user_id]['longitude'] = longitude
                        d[user_id]['latitude'] = latitude
                        m_given = "Выберите тип карты: \n 1.схема \n 2.спутник \n 3.гибрид"
                vk.messages.send(user_id=event.obj.message['from_id'], message=m_given,
                                 random_id=random.randint(0, 2 ** 64))
            elif d[user_id]['stage'] == 2:
                if m_took not in maps.keys():
                    d[user_id]['stage'] -= 1
                    vk.messages.send(user_id=event.obj.message['from_id'], message="Правильно введите тип карты!",
                                     random_id=random.randint(0, 2 ** 64))
                else:
                    params = {
                        "ll": str(d[user_id]['longitude']) + ',' + str(d[user_id]['latitude']),
                        "l": maps[m_took][0],
                        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                        'z': '12'
                    }
                    geocoder_server = "http://static-maps.yandex.ru/1.x/"
                    response = requests.get(geocoder_server, params=params)
                    print(response.url)
                    d[user_id]['filename'] = f"static/img/map{d[user_id]['request']}.{maps[m_took][1]}"
                    with open(d[user_id]['filename'], "wb") as file:
                        file.write(response.content)
                    send_photo(d[user_id]['filename'], user_id)


if __name__ == '__main__':
    main()
