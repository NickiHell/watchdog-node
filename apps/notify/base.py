import os


class BaseNotifier:
    def __init__(self):
        ...

    def notify(self, msg: str) -> None:
        os.system(msg)
