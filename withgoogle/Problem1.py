import numpy as np



def solution(g):
    grid = np.array(g, dtype=bool)
    height, width = grid.shape
    vectors, extended = get_vectors(height)
    count = np.ones(vectors.shape[0], dtype=int)

    for column in range(width):
        this_column = grid[:,column]
        temp = extended == this_column
        temp = np.all(temp, axis=2)
        temp = temp * count[:,None]
        count = temp.sum(axis=0)
    print(sum(count))

def get_vectors(height):
    rows = np.array(range(2 ** (height + 1)), dtype=int)
    columns = np.array(range(height + 1), dtype=int)
    result = rows[:,None] & (1 << columns) != 0
    result = result.astype(int)
    result = result[:,:-1] + result[:,1:]
    extended = (result[:,None,:] + result[None,:,:] == 1)
    return result, extended



if __name__ == '__main__':
    solution([[True, False, True, False, False, True, True, True],
                       [True, False, True, False, False, False, True, False],
                       [True, True, True, False, False, False, True, False],
                       [True, False, True, False, False, False, True, False],
                       [True, False, True, False, False, True, True, True]])


