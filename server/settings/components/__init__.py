# built-in
from pathlib import Path

# external
from decouple import AutoConfig


BASE_DIR = Path(__file__).parent.parent.parent.parent

config = AutoConfig(search_path=BASE_DIR.joinpath('config'))
