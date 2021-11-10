from database import Database
from settings import *
from API import API


def main(ignore_exceptions):
    if (ignore_exceptions):
        while True:
            try:
                API.main()
            except SystemExit:
                import sys
                sys.exit()
            except:
                pass
    else:
        API.main()
            


if __name__ == "__main__":
    # import threading
    # t1 = threading.Thread(target=Database.startLoggingDatabaseData)
    # t1.start()
    
    try:
        import multiprocessing
        t1 = multiprocessing.Process(target=Database.startLoggingDatabaseData)
        t1.start()
        
        # t2 = threading.Thread(target=main, kwargs={'ignore_exceptions': False})
        main(False)
    except SystemExit:
        import sys
        t1.terminate()
        sys.exit()