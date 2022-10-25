FROM archlinux:base-devel AS dev_build


# Arrange
LABEL maintainer="NickiHell"
LABEL vendor="nickihell.online"

ARG user=netrider
ARG dev=false


# Arrange
ADD . /app/
COPY ./docker/django/entrypoint.sh /app/entrypoint.sh
COPY poetry.lock pyproject.toml /app/
RUN pacman -Syyu --needed --noconfirm git rsync python reflector
RUN useradd --system --create-home $user
RUN echo "$user ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/$user
USER $user
WORKDIR /app/
RUN sudo chown $user:$user /app -R


# Act
RUN git clone https://aur.archlinux.org/yay.git \
  && cd yay \
  && makepkg -sri --needed --noconfirm \
  && cd /app \
  && rm -rf .cache yay


# Install deps
RUN sudo reflector --latest 25  --sort rate --country Russia --save /etc/pacman.d/mirrorlist
RUN yay -S base-devel git htop vim zsh tmux python tree yay dockerize python-psycopg python-pip --noconfirm
RUN yay -S make python-poetry bash brotli curl gettext python-setuptools python-psycopg2 --noconfirm
RUN pip install poetry
RUN if [ "${dev}" = "true" ] ;then poetry install ;else poetry install --no-dev ;fi

RUN python ./manage.py compilemessages
CMD ["sh "]
