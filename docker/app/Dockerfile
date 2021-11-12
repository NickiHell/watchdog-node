FROM python:3.9-slim-buster AS development_build



ENV BUILD_ONLY_PACKAGES='wget' \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # poetry:
  POETRY_VERSION=1.1.7 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  PATH="$PATH:/root/.poetry/bin"


RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    bash \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev \
    $BUILD_ONLY_PACKAGES \
  && curl -sSL 'https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py' | python \
  && poetry --version \
  && apt-get remove -y $BUILD_ONLY_PACKAGES \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml

RUN poetry install --no-interaction --no-ansi

COPY ./docker/entrypoint.sh entrypoint.sh
COPY ./app/ /app/app


ENTRYPOINT ["bash", "entrypoint.sh"]
