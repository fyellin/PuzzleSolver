import datetime
import multiprocessing
import random
from time import sleep
from typing import Any

from solver import PlayfairSolver


def init(l):
    global lock
    lock = l

def do_work(i, lock):
    sleep(random.uniform(1, 3))
    with lock:
        print(f"Looking at {i}")

def runner():
    lock = multiprocessing.Lock()
    with multiprocessing.Pool(initializer=init, initargs=(lock,)) as pool:
        for i in range(15):
            pool.apply_async(do_work, (i,))
        pool.close()
        pool.join()

def runner():
    lock = multiprocessing.Lock()
    pool =  multiprocessing.Pool(initializer=init, initargs=(lock,))
    for i in range(15):
        pool.apply_async(do_work, (i, None))
    pool.close()
    pool.join()
    pool.terminate()

def runner():
    print(multiprocessing.current_process().authkey)
    with multiprocessing.Manager() as manager:
        lock = multiprocessing.Lock()
        pool =  multiprocessing.Pool()
        for i in range(15):
            pool.apply_async(do_work, (i, lock))
        pool.close()
        pool.join()

class Timer:
    def __enter__(self) -> 'Timer':
        self.start = datetime.datetime.now()
        return self

    def __exit__(self, *args: Any) -> 'None':
        self.end = datetime.datetime.now()
        self.interval = self.end - self.start
        print(self.interval)


if __name__ == '__main__':
        with Timer():
            PlayfairSolver.test(debug=True)
