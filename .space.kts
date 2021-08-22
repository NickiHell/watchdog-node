job("Tests") {
    container(displayName = "Python Cotainer", image = "python:3.9.6-bullseye") {
    shellScript {
            content = """
                ls
                apt update
                apt install tree
            """
        }
}}