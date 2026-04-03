import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from keep_alive import keep_alive
from scheduler import main

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
