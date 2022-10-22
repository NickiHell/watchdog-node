# syntax = docker/dockerfile:1
# This Dockerfile uses multi-stage build to customize DEV and PROD images:
# https://docs.docker.com/develop/develop-images/multistage-build/

FROM python:3.10.8 AS development_build

LABEL maintainer="nickihell.online"
LABEL vendor="nickihell.online"

# `DJANGO_ENV` arg is used to make prod / dev builds:
ARG DJANGO_ENV

ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  # dockerize:
  DOCKERIZE_VERSION=v0.6.1 \
  # tini:
  TINI_VERSION=v0.19.0 \
  # poetry:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# System deps (we don't use exact versions because it is hard to update them,
# pin when needed):
# hadolint ignore=DL3008
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    bash \
    brotli \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev \
  # Installing `dockerize` utility:
  # https://github.com/jwilder/dockerize
  && curl -sSLO "https://github.com/jwilder/dockerize/releases/download/${DOCKERIZE_VERSION}/dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz" \
  && tar -C /usr/local/bin -xzvf "dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz" \
  && rm "dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz" && dockerize --version \
  # Installing `tini` utility:
  # https://github.com/krallin/tini
  # Get architecture to download appropriate tini release:
  # See https://github.com/wemake-services/wemake-django-template/issues/1725
  && dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
  && curl -o /usr/local/bin/tini -sSLO "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${dpkgArch}" \
  && chmod +x /usr/local/bin/tini && tini --version \
  # Installing `poetry` package manager:
  # https://github.com/python-poetry/poetry
  && curl -sSL https://install.python-poetry.org | python3 - \
  && poetry --version \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Static and media files:
RUN mkdir -p '/var/www/django/static' '/var/www/django/media'
RUN chown root:root '/var/www/django/static' '/var/www/django/media'

# Copy only requirements, to cache them in docker layer
COPY ./poetry.lock ./pyproject.toml /app/

# Project initialization:
# hadolint ignore=SC2046
RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
  echo "$DJANGO_ENV" \
  && poetry version \
  # Install deps:
  && poetry run pip install -U pip \
  && poetry install \
    $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only core'; fi) \
    --no-interaction --no-ansi

# This is a special case. We need to run this script as an entry point:
COPY ./docker/django/entrypoint.sh /app/docker-entrypoint.sh
COPY ./manage.py /app/manage.py

# Setting up proper permissions:
RUN chmod +x '/app/docker-entrypoint.sh'

# We customize how our app is loaded with the custom entrypoint:
ENTRYPOINT ["tini", "--", "/app/docker-entrypoint.sh"]


# The following stage is only for production:
# https://wemake-django-template.readthedocs.io/en/latest/pages/template/production.html
FROM development_build AS production_build
COPY . /app
