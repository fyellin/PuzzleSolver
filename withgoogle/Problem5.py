import itertools

def solution(numbers):
    length = len(numbers)
    pairs = [(i, j) for i, j in itertools.combinations(range(length), 2) if numbers[j] % numbers[i] == 0]

    count = [1] * length
    for _ in range(2):
        temp = [0] * length
        for (i, j) in pairs:
            temp[i] += count[j]
        count = temp

    return sum(count)

if __name__ == '__main__':
    print(solution([1, 2, 3, 4, 5, 6]))
    print(solution([1, 1, 1]))
