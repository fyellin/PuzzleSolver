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


LINES =  """
1 10a × (4d + 4d) × 11d (6) 
4 4a × (4a + 2d + 4d) (4) 
6 13d × 16d + 11d (5)
8 18a + 9a + 9a (4)
9 9a × (16a + 4d + 4d) (6)
10 11a × 2d (3)
11 2d + 7d – 15d (3)
12 11d × (12a + 10d – 1d) (5)
14 12a × (10a + 16d) + 2d (5)
16 1a + 18a – 16d (4)
17 16a + 15d – 4d (3)
18 1d × 11d (6)
1 1a – 10a – 10a (4)
2 2d + 4d + 15d (3)
3 18a + 18a – 11a – 2d (4)
4 6a – 17a + 4d (3)
5 5d × 16d × (4d – 11a – 2d) (6) 
7 9a + 16a + 13d (4)
10 11a + 18a + 15d (4)
11 2d × 11d × (4a + 11a + 2d) (6)
12 1a – 4a – 4a (4)
13 17a × (17a + 17a + 3d) (5) 
15 1a + 3d – 14a (4)
16 9a + 5d (3)
"""

GRID = """
X.XXXX
XX.X..
.X..X.
X.X..X
XX.X..
X.X...
"""

def runit():
    import re
    lines = [line.strip() for line in LINES.splitlines() if line]
    a = {1: 7814, 4: 41, 6: 523, 8:378, 9:802, 10:29, 11:23, 12: 728, 14:873, 16:907, 17:93, 18:2184}
    d = {1: 756, 11:289, 7:283, 15:73, 2: 13, 12:732, 3:432, 16:91, 4:47, 10:280, 5:189, 13:574}
    for line in lines:
        match = re.fullmatch(r'(\d+) (.+) \((\d+)\)', line)
        clue = match.group(1)
        equation = match.group(2)
        length = int(match.group(3))
        equation = re.sub(r'(\d+)([ad])', r'\2[\1]', equation)
        equation = equation.replace('×', '*').replace('–', '-')
        value = str(eval(equation, dict(a=a, d=d)))
        assert len(value) == length
        value2 = re.sub(r'(\d+)\1', r'\1', value)
        print(clue, value, value2, equation)

def runit():
    for x in range(100, 200):
        y = 21 * (41 + 41) * x
        t = str(y)

        if len(t) != 6: continue
        if any(t[i:i+2] == t[i+2:i+4] for i in range(len(t) - 3)):
            print(x, y)




if __name__ == '__main__':
    runit()
