job("Tests") {
    container(displayName = "Python Cotainer", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
                $HOME/.poetry/bin/poetry shell
                task tests
            """
        }
}}