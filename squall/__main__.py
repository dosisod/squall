import sys
from pathlib import Path

from squall.main import main as _main


def main() -> None:
    _main(Path(x) for x in sys.argv[1:])
