import itertools

TRIANGLES = set(i * (i + 1) // 2 for i in range(1, 50))
SQUARES = set(i * i for i in range(1, 50))

def check2():
    for low in range(10, 100):
        for high in range(low + 7, 100, 7):
            delta = (high - low) // 7
            items = list(range(low, high + 1, delta))
            if sum(items) % 100 == 0:
                print(items, sum(items), [x for x in items if x in TRIANGLES], [x for x in items if x in SQUARES])

def check3():
    results = [[] for _ in range(10)]
    for x in sorted(TRIANGLES):
        if 100 <= x <= 999:
            results[(x % 100) // 10].append(x)
    for i, value in enumerate(results):
        print(i, value)


def subsets(x):
    for count in range(0, len(x) + 1):
        yield from itertools.combinations(x, count)


"""
[11, 15, 19, 23, 27, 31, 35, 39] 200 [15] []
[13, 20, 27, 34, 41, 48, 55, 62] 300 [55] []
[15, 25, 35, 45, 55, 65, 75, 85] 400 [15, 45, 55] [25]
[18, 20, 22, 24, 26, 28, 30, 32] 200 [28] []
[20, 25, 30, 35, 40, 45, 50, 55] 300 [45, 55] [25]
[22, 30, 38, 46, 54, 62, 70, 78] 400 [78] []
[27, 30, 33, 36, 39, 42, 45, 48] 300 [36, 45] [36]
[29, 35, 41, 47, 53, 59, 65, 71] 400 [] []
[31, 40, 49, 58, 67, 76, 85, 94] 500 [] [49]
[34, 35, 36, 37, 38, 39, 40, 41] 300 [36] [36]
[36, 40, 44, 48, 52, 56, 60, 64] 400 [36] [36, 64]
[38, 45, 52, 59, 66, 73, 80, 87] 500 [45, 66] []
[43, 45, 47, 49, 51, 53, 55, 57] 400 [45, 55] [49]
[45, 50, 55, 60, 65, 70, 75, 80] 500 [45, 55] []
[52, 55, 58, 61, 64, 67, 70, 73] 500 [55] [64]
[54, 60, 66, 72, 78, 84, 90, 96] 600 [66, 78] []
[59, 60, 61, 62, 63, 64, 65, 66] 500 [66] [64]
[61, 65, 69, 73, 77, 81, 85, 89] 600 [] [81]
[68, 70, 72, 74, 76, 78, 80, 82] 600 [78] []
[77, 80, 83, 86, 89, 92, 95, 98] 700 [] []
[84, 85, 86, 87, 88, 89, 90, 91] 700 [91] []

must have both a triangular number and a square, and they're different

[15, 25, 35, 45, 55, 65, 75, 85] 400 [15, 45, 55] [25]
[20, 25, 30, 35, 40, 45, 50, 55] 300 [45, 55] [25]
[27, 30, 33, 36, 39, 42, 45, 48] 300 [36, 45] [36]
[36, 40, 44, 48, 52, 56, 60, 64] 400 [36] [36, 64]
[43, 45, 47, 49, 51, 53, 55, 57] 400 [45, 55] [49]
[52, 55, 58, 61, 64, 67, 70, 73] 500 [55] [64]
[59, 60, 61, 62, 63, 64, 65, 66] 500 [66] [64]

kill the last two because obviously can't make 100
kill 27... 48 because there is no way to get two numbers ≥ 27 to add to 100-48

[15, 25, 35, 45, 55, 65, 75, 85] 400 [15, 45, 55] [25]
[20, 25, 30, 35, 40, 45, 50, 55] 300 [45, 55] [25]
[36, 40, 44, 48, 52, 56, 60, 64] 400 [36] [36, 64]
[43, 45, 47, 49, 51, 53, 55, 57] 400 [45, 55] [49]

The first digit of the square must be the last digit of one of the other two digits:

[36, 40, 44, 48, 52, 56, 60, 64] 400 [36] [36, 64]
10D is 36  (triangular)
12D is 64
11A is 56
[40, 44, 48, 52, 60] 400 [36] [36, 64]
Last digit of 1D is first digit of 5A
1D is 44
5A is 48
[40, 52, 60]  7A, 8A, 3D, 
7A must be 52, since 2D is a palindrome, and so 7A can't end in 0

"""

if __name__ == '__main__':
    check3()
