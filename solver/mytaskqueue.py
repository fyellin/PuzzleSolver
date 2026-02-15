import hashlib
import io
import pickle
import queue
import struct
from collections import deque
from multiprocessing import Condition, Lock, RLock, shared_memory

# These are protected by state_lock
START_OFFSET = 0
END_OFFSET = 1
NEXT_GET_OFFSET = 2
QSIZE_OFFSET = 3
TASK_NOT_DONE_OFFSET = 4
GET_COUNT_OFFSET = 5
PUT_COUNT_OFFSET = 6
GET_WAIT_COUNT_OFFSET = 7

# These are protected by stats_lock
MAX_COUNT_OFFSET = 10
MAX_LENGTH_OFFSET = 11
PUT_FULL_COUNT_OFFSET = 12
TOTAL_SIZE_OFFSET = 13

NORMAL_SIZE = 0
WRITING_IN_PROGRESS = 1  # a PUT has allocated this spot, but not written to it yet
READER_WAITING = 2  # a GET wants this spot, and is waiting for a PUT to finish.
WAITING_FOR_GC = 4  # a GET has read this data, and it can be gc'ed when possible.

class MyTaskQueue:
    def __init__(self, *, size, debug=False):
        self.memory = shared_memory.SharedMemory(create=True, size=size)
        self.state_lock = RLock()
        self.stats_lock = Lock()
        self.print_lock = Lock()
        self.is_not_full = Condition(self.state_lock)
        self.is_not_empty = Condition(self.state_lock)
        self.all_tasks_done = Condition(self.state_lock)
        self.waiting_for_write = Condition(self.state_lock)
        self.state, self.data = self.__initialize_buffers()
        for i in range(len(self.state)):
            self.state[i] = 0
        self.debug = debug
        self.hasher = hashlib.sha1
        # self.my_reader = ConcatenatedStream(self.data)

    def get(self, block=True):
        state = self.state
        data = self.data
        data_size = len(self.data)
        with self.state_lock:
            while (qsize := state[QSIZE_OFFSET]) <= 0:
                if not block:
                    raise queue.Empty
                else:
                    state[GET_WAIT_COUNT_OFFSET] += 1
                    self.is_not_empty.wait()
                    state[GET_WAIT_COUNT_OFFSET] -=1
            read_start = self.state[NEXT_GET_OFFSET]
            size, flags = struct.unpack_from("II", data, read_start)
            pickle_start = (read_start + 8) % data_size
            pickle_end = pickle_start + size # may be larger than data_size

            state[GET_COUNT_OFFSET] = get_count = state[GET_COUNT_OFFSET] + 1
            state[QSIZE_OFFSET] = qsize - 1
            state[NEXT_GET_OFFSET] = ((pickle_end + 7) & ~7) % data_size

            if flags & WRITING_IN_PROGRESS:
                struct.pack_into("II", data, read_start, size, flags | READER_WAITING)
                if self.debug:
                    with self.print_lock:
                        print(f"GET #{get_count}: Waiting for write to {pickle_start}-{pickle_end}")
                while flags & WRITING_IN_PROGRESS:
                    self.waiting_for_write.wait()
                    _size, flags, = struct.unpack_from("II", data, read_start)
                if self.debug:
                    with self.print_lock:
                        print(f"GET #{get_count}: Write is finished {read_start}-{pickle_end})")

        if pickle_end <= data_size:
            pickled_result = data[pickle_start:pickle_end]
        else:
            pickled_result = bytearray(size)
            middle = data_size - pickle_start
            pickled_result[0:middle] = data[pickle_start:]
            pickled_result[middle:] = data[:size - middle]
        try:
            result = pickle.loads(pickled_result)
        except pickle.UnpicklingError:
            with self.print_lock:
                print(f"GET ERROR #{get_count}: {pickle_start - 8:,} - {pickle_end:,} (size={size:,}) "
                    f"{self.hasher(pickled_result).hexdigest()}")
            raise

        with self.state_lock:
            struct.pack_into("II", data, read_start, size, WAITING_FOR_GC)
            initial_start = start = state[START_OFFSET]
            next_read = state[NEXT_GET_OFFSET]
            while start != next_read:
                size, flags = struct.unpack_from("II", data, start)
                if not (flags & WAITING_FOR_GC):
                    break
                start = ((start + size + 8 + 7) & ~7) % data_size
            if start != initial_start:
                if start == state[END_OFFSET]:
                    state[START_OFFSET] = state[END_OFFSET] = state[NEXT_GET_OFFSET] = 0
                else:
                    state[START_OFFSET] = start
                self.is_not_full.notify_all()

        if self.debug:
            with self.print_lock:
                print(f"GET #{get_count}: {pickle_start - 8:,} - {pickle_end:,} (size={size:,}) "
                      f"{self.hasher(pickled_result).hexdigest()}")
        return result

    def put(self, value, block=True):
        state = self.state
        data = self.data
        data_size = len(data)


        pickled_value = pickle.dumps(value)
        size = len(pickled_value)
        full_size = (8 + size + 7) & ~7
        with self.state_lock:
            while True:
                start, end = state[START_OFFSET], state[END_OFFSET]
                if end + full_size < start + (0 if start > end else data_size):
                    # We have space
                    break
                elif block:
                    self.is_not_full.wait()
                else:
                    state[PUT_FULL_COUNT_OFFSET] += 1
                    raise queue.Full

            # Claim our space in the queue.
            state[QSIZE_OFFSET] = qsize = state[QSIZE_OFFSET] + 1
            state[PUT_COUNT_OFFSET] = put_count = state[PUT_COUNT_OFFSET] + 1
            state[TASK_NOT_DONE_OFFSET] = state[TASK_NOT_DONE_OFFSET] + 1

            state[END_OFFSET] = (end + full_size) % data_size
            struct.pack_into("II", data, end, size, WRITING_IN_PROGRESS)
            self.is_not_empty.notify()

        # Do the actual copying of the data outside the lock. We own the bytes
        pickle_start = (end + 8) % data_size
        pickle_end = pickle_start + size  # may go over data_size
        if pickle_end <= data_size:
            data[pickle_start:pickle_end] = pickled_value
        else:
            first_size = data_size - pickle_start
            pickled_value = memoryview(pickled_value)  # so that slicing doesn't copy
            data[pickle_start:] = pickled_value[0:first_size]
            data[:size - first_size] = pickled_value[first_size:]

        with self.state_lock:
            _, flags = struct.unpack_from("II", data, end)
            flags &= ~WRITING_IN_PROGRESS
            struct.pack_into("II", data, end, size, flags)
            if flags & READER_WAITING:
                self.waiting_for_write.notify_all()
                if self.debug:
                    with self.print_lock:
                        print(f"PUT FOR GETTER#{put_count}: {end:,} - {pickle_end:,} "
                              f"(size={size:,}) {self.hasher(pickled_value).hexdigest()}")
        with self.stats_lock:
            state[MAX_COUNT_OFFSET] = max(state[MAX_COUNT_OFFSET], qsize)
            state[MAX_LENGTH_OFFSET] = max(state[MAX_LENGTH_OFFSET], size)
            state[TOTAL_SIZE_OFFSET] += size

        if self.debug:
            with self.print_lock:
                print(f"PUT #{put_count}: {end:,} - {pickle_end:,} "
                      f"(size={size:,}) {self.hasher(pickled_value).hexdigest()}")

    def is_get_waiting(self):
        with self.state_lock:
            return self.state[GET_WAIT_COUNT_OFFSET] > 0

    def task_done(self):
        with self.state_lock:
            value = self.state[TASK_NOT_DONE_OFFSET] - 1
            self.state[TASK_NOT_DONE_OFFSET] = value
            if value <= 0:
                self.all_tasks_done.notify_all()

    def join(self):
        with self.all_tasks_done:
            while self.state[TASK_NOT_DONE_OFFSET] > 0:
                self.all_tasks_done.wait()

    def close(self, last=False):
        if last:
            print(f"MAX_COUNT = {self.state[MAX_COUNT_OFFSET]:,}")
            print(f"MAX_LENGTH = {self.state[MAX_LENGTH_OFFSET]:,}")
            print(f"PUT_FULL = {self.state[PUT_FULL_COUNT_OFFSET]:,}")
            print(f"TOTAL_SIZE = {self.state[TOTAL_SIZE_OFFSET]:,}")
        self.data = self.state = None
        self.memory.close()
        if last:
            self.memory.unlink()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['state']
        del state['data']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.state, self.data = self.__initialize_buffers()

    def __initialize_buffers(self):
        buffer = self.memory.buf
        state = buffer.cast("Q")[-16:]
        data = buffer[:-state.nbytes]
        return state, data

    def __str__(self):
        globals = self.state
        count, start, end, not_done = [
            globals[i] for i in (QSIZE_OFFSET, START_OFFSET,
                                 END_OFFSET, TASK_NOT_DONE_OFFSET)]
        return f"<Queue {count=:,} {not_done=:,} range = {start:,} - {end:,}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close(True)

class ConcatenatedStream(io.RawIOBase):
    def __init__(self, data):
        self.data = data
        self.length = len(data)
        self.pos = 0

    def readinto(self, buffer:bytearray):
        total_read = 0

        while total_read < len(buffer):
            remaining_in_view = self.length - self.pos
            to_read = min(remaining_in_view, len(buffer) - total_read)
            buffer[total_read:total_read + to_read] = \
                self.data[self.pos:self.pos + to_read]
            total_read += to_read
            self.pos += to_read
            if self.pos >= self.length:
                self.pos = 0

        return len(buffer)

    def readable(self):
        return True

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        if whence == 0 or whence == 2:
            self.pos = offset % self.length
        else:
            self.pos = (self.pos + offset) % self.length

    def close(self):
        self.data = None


def run_test():
    my_queue = deque()
    task_queue = MyTaskQueue(size=1000,)

    count = 0
    def get_item():
        nonlocal count
        count -= 1
        return [count] * 200

    try:
        while True:
            temp = get_item()
            task_queue.put(temp, False)
            my_queue.append(temp)
    except queue.Full:
        print(f"Pushed {len(my_queue)} items")
    count = len(my_queue)
    for i in range(5000 * count):
        assert task_queue.get() == my_queue.popleft()
        temp = get_item()
        task_queue.put(temp, False)
        my_queue.append(temp)
    while my_queue:
        assert task_queue.get() == my_queue.popleft()
    try:
        task_queue.get(False)
        assert True, "Expected to fail"
    except queue.Empty:
        pass

    task_queue.close(True)


if __name__ == '__main__':
    from datetime import datetime
    start = datetime.now()
    run_test()
    end = datetime.now()
    print(end - start)
