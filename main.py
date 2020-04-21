import logging
from app import App


logging.basicConfig(level=logging.DEBUG)  # , format='%(asctime) - %(level) - %(message)')


if __name__ == '__main__':
    App().main()
