FROM archlinux:latest AS dev_build


# ENVS
ARG DJANGO_ENV=dev

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Dependencies
RUN pacman -Syyu base-devel git python python-poetry zsh gcc --noconfirm
# RUN git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si

# Directories
WORKDIR /app
ADD . /app

# Project dependencies
RUN poetry config virtualenvs.create false
RUN poetry install $(test "DJANGO_ENV" == prod && echo " --without group.suka.dev") --no-interaction --no-ansi


CMD ["/bin/zsh -c ", "docker/django/entrypoint.sh"]
