import itertools
import uuid

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

if __name__ == '__main__':
    run_test()


