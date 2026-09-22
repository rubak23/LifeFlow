"""PyCharm entry point for the complete LifeFlow application."""

import os
from server import run


if __name__ == "__main__":
    run(int(os.environ.get("PORT", "4173")))
