
FROM archlinux:latest AS dev_build

ARG DJANGO_ENV=development

ENV YOUR_ENV=${ENV}
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100


RUN pacman -Syyu base-devel git python python-poetry python-psycopg2 postgresql gcc --noconfirm
# RUN git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si


WORKDIR /app
ADD . /app


RUN poetry config virtualenvs.create false \
  && poetry install $(test "DJANGO_ENV" == production && echo "--no-dev") --no-interaction --no-ansi


CMD ["sh", "./docker/django/entrypoint.sh"]
