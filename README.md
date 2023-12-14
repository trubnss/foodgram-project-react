# **_Foodgram_**
Foodgram, «Продуктовый помощник». Онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей


### _Развернуть проект на удаленном сервере:_

**_Клонировать репозиторий:_**
```
git@github.com:trubnss/Foodgram.git
```
Установить на сервере Docker

Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra (команды выполнять находясь в папке infra)


### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха



**_В проекте используется файл конфигурации .env, данные для заполнения:_**
```
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DB_HOST=
DB_PORT=
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
```


**_Документация будет доступна по адресу: http://foodgramfortraining.zapto.org/api/docs/_**

**_Данные для ревью_**
```commandline
foodgramfortraining.zapto.org
admin:  yc-user@yandex.fack
pass: JlOv3bJ-5z
```

