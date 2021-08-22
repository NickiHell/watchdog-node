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
        var HOME = "$HOME"
    			
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                source "$HOME/.poetry/env"
                task pytest
            """
        }
	}
    container(displayName = "Mypy", image = "python:3.9.6-bullseye") {
    shellScript {
        	interpreter = "/bin/bash"
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                source .poetry/env
                bash poetry/bin/poetry shell
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