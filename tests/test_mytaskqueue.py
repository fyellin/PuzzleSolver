import queue
from collections import deque

import pytest

from solver.mytaskqueue import MyTaskQueue


def test_put_get_wrapping():
    """Fill the queue, then cycle through puts/gets to exercise wrap-around."""
    my_queue = deque()
    task_queue = MyTaskQueue(size=1000)

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
        pass

    count = len(my_queue)
    for _i in range(5000 * count):
        assert task_queue.get() == my_queue.popleft()
        temp = get_item()
        task_queue.put(temp, False)
        my_queue.append(temp)

    while my_queue:
        assert task_queue.get() == my_queue.popleft()

    with pytest.raises(queue.Empty):
        task_queue.get(False)

    task_queue.close(True)
