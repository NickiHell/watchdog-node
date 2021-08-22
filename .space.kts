job("Tests") {
    container(displayName = "Python Cotainer", image = "ubuntu")
    shellScript {
            content = """
                ls
                apt update
                apt install tree
            """
        }
}