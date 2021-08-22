job("QA and Linters") {
    container(displayName = "Tests", image = "python:3.9.6-bullseye") {
    			
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                /root/.poetry/bin/poetry install
                /root/.poetry/bin/poetry run task pytest
            """
        }
	}
    container(displayName = "Mypy", image = "python:3.9.6-bullseye") {
    shellScript {
        	interpreter = "/bin/bash"
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                /root/.poetry/bin/poetry install
                /root/.poetry/bin/poetry run task mypy
            """
        }
	}
    container(displayName = "FlakeHell", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                /root/.poetry/bin/poetry install
                /root/.poetry/bin/poetry run task flakehell
            """
        }
	}
}