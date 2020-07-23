#!/bin/sh

docker-compose run web /root/.poetry/bin/poetry run django-admin startproject eventsusers .
sudo mv -f settings.py eventsusers/settings.py
sudo chown -R $USER:$USER .
