FROM archlinux:latest AS dev_build

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Dependencies
RUN pacman -Syyu base base-devel sudo git python python-setuptools python-poetry busybox wget zsh gcc --noconfirm

# Directories
WORKDIR /app
ADD . /app

# Project dependencies
RUN poetry config virtualenvs.create false
# RUN poetry install $(test "DJANGO_ENV" == prod && echo " --without group.dev") --no-interaction --no-ansi
RUN poetry install --no-interaction --no-ansi


#CMD ["./docker/django/entrypoint.sh"]
