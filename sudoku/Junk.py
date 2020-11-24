import functools
import multiprocessing as mp

import numpy as np


def test(name, t_dict):
    t_dict = t_dict.copy()
    t_dict['a'] = name
    return t_dict

def mp_func(func, iterator ,**kwargs):
    f_args = functools.partial(func, **kwargs)
    pool = mp.Pool(mp.cpu_count())
    res = pool.map(f_args, iterator)
    pool.close()
    return res

def go():
    mod =dict()

    m =33
    res = mp_func(func=test, iterator=np.arange(m), t_dict=mod)
    for di in res:
        print(di['a'])

if __name__ == '__main__':
    go()

