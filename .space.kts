job("QA and Linters") {
    container(displayName = "Isort", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                .poetry/bin/poetry shell
                task isort
            """
        }
	}
    container(displayName = "Tests", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                .poetry/bin/poetry shell
                task pytest
            """
        }
	}
    container(displayName = "Mypy", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                source $HOME/.poetry/env
                task mypy
            """
        }
	}
    container(displayName = "FlakeHell", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                .poetry/bin/poetry shell
                task flakehell
            """
        }
	}
}