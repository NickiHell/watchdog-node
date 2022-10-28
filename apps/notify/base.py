import os
from abc import ABC


class BaseNotifier(ABC):

    def __init__(self):
        ...

    def notify(self, msg: str) -> None:
        os.system(msg)
