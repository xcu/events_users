from python:3.8
ENV PYTHONUNBUFFERED 1
RUN mkdir /src
WORKDIR /src
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | POETRY_PREVIEW=1 python
RUN git clone https://github.com/xcu/events_users.git
WORKDIR /src/events_users
RUN /root/.poetry/bin/poetry install --no-dev
