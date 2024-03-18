# **_Foodgram_**
Foodgram, Онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей. Так же сервись имеет возможность добовлять рецеты в продуктовую корзину, для получения списка ингредиентов.


### _Развернуть проект на удаленном сервере:_

**_Клонировать репозиторий:_**
```
git@github.com:trubnss/foodgram-project-react.git
```
Для равертывания проекта на сервере можно использовать Docker, исполнительный файл:
```commandline
infra/docker-compose.yml
```
Так же в проекте используется переменное окружение. Структура файла env:
```commandline
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
DB_HOST
DB_PORT
SECRET_KEY
DEBUG
ALLOWED_HOSTS
```
Список ингредиентов находиться в /backend/data/ingredients, данные из этой дерриктории вносятся в БД с помощью команды:
```commandline
python manage.py load_ingredients
```

**_Документация будет доступна по адресу: http://example.com/api/docs/_**
