#!/bin/sh

docker-compose run web /root/.poetry/bin/poetry run python manage.py makemigrations events_users
docker-compose run web /root/.poetry/bin/poetry run python manage.py migrate

