FROM ros:iron


WORKDIR /app

RUN apt-get update
RUN apt-get upgrade -y
RUN apt install python3 python3-venv python3-wheel python3-pip python3-setuptools busybox curl build-essential -y --no-install-recommends

COPY pyproject.toml /app/pyproject.toml
COPY requirements.txt /app/requirements.txt

RUN pip
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["bash"]
