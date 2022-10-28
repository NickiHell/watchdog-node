
FROM archlinux:latest AS dev_build

ARG ENV=dev

ENV YOUR_ENV=${ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100


# Initial deps
RUN pacman -Syyu base-devel git python-poetry python-psycopg2 gcc --noconfirm --needed
RUN git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si


# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml /app/


# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install $(test "ENV" == production && echo "--no-dev") --no-interaction --no-ansi


# Creating folders, and files for a project:
COPY . /app
CMD ["/bin/zsh"]
