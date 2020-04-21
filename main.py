import logging
import sys
from app import App


verbose = '-v' in sys.argv
logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)  # , format='%(asctime) - %(level) - %(message)')


if __name__ == '__main__':
    App().main()
