job("QA and Linters") {
    container(displayName = "Isort", image = "python:3.9.6-bullseye") {
    shellScript {
        	interpreter = "/bin/bash"
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                /root/.poetry/bin/poetry shell
                task isort
            """
        }
	}
    container(displayName = "Tests", image = "python:3.9.6-bullseye") {
    			
    shellScript {
            content = """
                ls
            """
        }
	}
    container(displayName = "Mypy", image = "python:3.9.6-bullseye") {
    shellScript {
        	interpreter = "/bin/bash"
            content = """
                ls
            """
        }
	}
    container(displayName = "FlakeHell", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                ls
            """
        }
	}
}