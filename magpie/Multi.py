import datetime
import multiprocessing
import random
from time import sleep


def init(l):
    global lock
    lock = l

def print_worker(i):
    sleep(random.uniform(1, 2))
    with lock:
        # The lock is just so that the print statements don't get interweaved with each other.  Stops multiple
        # threads for all writing at the same time to the terminal.
        print(f"Looking at {i} in thread {multiprocessing.current_process().name}")
    return i, i * i

def multiply_worker(i, j):
    sleep(random.uniform(1, 2))
    with lock:
        print(f"{i} * {j} = {i * j}")
    return i * j


def runner():
    lock = multiprocessing.Lock()
    with multiprocessing.Pool(initializer=init, initargs=(lock,)) as pool:
        # pool.map waits until all results are done
        # pool.imap returns an iterator, but in order
        # pool.imap_unordered returns an iterator, in a random order
        # pool.map_async
        temp = pool.starmap_async(multiply_worker, ((i, i + 1) for i in range(20)))
        print(temp.get())

        pool.close()
        pool.join()


if __name__ == '__main__':
    start = datetime.datetime.now()
    runner()
    end = datetime.datetime.now()
    print(end - start)
