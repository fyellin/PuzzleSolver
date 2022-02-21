import itertools
import uuid
from typing import Optional, TypeGuard

import redis
import redisbloomfilter


def run_test():
    client = redis.Redis()
    bloom = redisbloomfilter.RedisBloomFilter("my_filter", 1_000_000, 0, client)
    bloom.initialize()

    for round in itertools.count(1):
        strings = [str(uuid.uuid4()) for _ in range(1000)]
        for string in strings:
            bloom.put(string)
        count = bloom.count()
        print(round, count)
        if count != 1000 * round:
            break

        if count > 1_000_000:
            break

def print_calendar(d, n):
    line = (d + n) // 7

    print("Sun", "Mon", "Tue", "Wed", "Thr", "Fri", "Sat")
    date = 1
    for i in range(6):
        if i < d - 1:
            print(" " * 3, end=" ")
        else:
            print(" " * 2 + str(date), end=" ")
            date += 1
    print(f'{date:>3}')
    date += 1

    for i in range(1, line):
        for _ in range(6):
            print(" " * (3-len(str(date))) + str(date), end=" ")
            date += 1
        print(" " * (3-len(str(date))) + str(date))
        date += 1
    for _ in range((d + n - 2) % 7):
        print(" " * (3-len(str(date))) + str(date), end=" ")
        date += 1
    print(" " * (3-len(str(date))) + str(date))
    print("xxxx")


x = [j for i in range(11) for j in ([1] if i == 0 else [*([0]*i), 1])]
x = [j for i in range(11) for j in itertools.chain((1,), itertools.repeat(0, i))]
print(x)
