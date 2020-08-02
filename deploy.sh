#!/bin/sh

docker-compose run web /root/.poetry/bin/poetry run python manage.py makemigrations accounts
docker-compose run web /root/.poetry/bin/poetry run python manage.py migrate

