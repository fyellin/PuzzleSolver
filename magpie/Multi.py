import datetime
import multiprocessing
import random
from time import sleep

class Temp(str):
    pass


def init(l):
    global lock
    lock = l

def worker(i):
    sleep(random.uniform(1, 3))
    with lock:
        print(f"Looking at {i} in thread {multiprocessing.current_process().name}")


def runner():
    lock = multiprocessing.Lock()
    with multiprocessing.Pool(initializer=init, initargs=(lock,)) as pool:
        pool.map_async(worker, range(15))
        pool.apply_async(worker, ("/tmp/foo.ps",))
        pool.apply_async(worker, ("/tmp/bar",))
        pool.close()
        pool.join()


if __name__ == '__main__':
    start = datetime.datetime.now()
    runner()
    end = datetime.datetime.now()
    print(end - start)
