# **_Foodgram_**
Foodgram — онлайн-сервис и API для него. На этом сервисе пользователи публикуют свои рецепты, подписываются на публикации других пользователей. Также сервис имеет возможность добавлять рецепты в продуктовую корзину для получения списка ингредиентов.

### _Развернуть проект на удаленном сервере:_

Для равертывания проекта на сервере можно использовать Docker, исполнительный файл:
```commandline
infra/docker-compose.yml
```
Структура файла .env:
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
Список ингредиентов находится в /backend/data/ingredients. Данные из этой директории вносятся в БД с помощью команды:
```commandline
python manage.py load_ingredients
```

**_Документация будет доступна по адресу: http://example.com/api/docs/_**
