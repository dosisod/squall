from squall.main import main as _main
from squall.settings import Settings


def main() -> None:
    _main(Settings.from_args())
