from __future__ import annotations

import heapq
import itertools
from functools import cache
from collections.abc import Sequence
from typing import NamedTuple, Protocol, cast


class Token (Protocol):
    id: int


class TokenGenerator:
    disks: int
    cache: dict[str, Token]

    def __init__(self, disks):
        self.disks = disks
        self.cache = {}
        for tower in Tower.all_towers(disks):
            tower_id = self.__normalize_id(tower.id)
            if tower_id not in self.cache:
                token = self._Token(tower_id, len(self.cache))
                self.cache[tower_id] = cast(Token, token)

    def __normalize_id(self, string: str) -> str:
        last = string[-1]
        next_last = next((x for x in reversed(string) if x != last), None)
        if next_last is None:
            return string.replace(last, 'A')
        next_next_last = ({'A', 'B', 'C'} - {last, next_last}).pop()
        table = str.maketrans(last + next_last + next_next_last, "ABC")
        return string.translate(table)

    def get_all_tokens(self):
        result = set(self.cache.values())
        assert len(result) == len(self.cache)
        return result

    def from_tower(self, tower: Tower) -> Token:
        id = self.__normalize_id(tower.id)
        return self.cache[id]

    class _Token (NamedTuple):
        id: id
        count: int

        @cache
        def __str__(self) -> str:
            return self.id

        def __eq__(self, other) -> bool:
            return self.id == other.id

        def __hash__(self) -> int:
            return hash(self.id)


class Tower (NamedTuple):
    id: str

    @cache
    def __str__(self):
        return self.id

    def __repr__(self):
        return f'Tower({self.id})'

    @staticmethod
    def all_towers(disks: int) -> Sequence[Tower]:
        return [Tower(''.join(info)) for info in itertools.product("ABC", repeat=disks)]

    @staticmethod
    def from_stacks(t1: tuple[int, ...], t2: tuple[int, ...], t3: tuple[int, ...]) -> Tower:
        count = len(t1) + len(t2) + len(t3)
        info = ['A' if x in t1 else 'B' if x in t2 else 'C' for x in range(1, count + 1)]
        return Tower(''.join(info))

    @cache
    def get_neighbors(self) -> list[tuple[int, Tower]]:
        id = self.id
        first = id[0]
        results = [(1, Tower(x + id[1:])) for x in 'ABC' if x != first]
        for index, second in enumerate(self.id):
            if second != first:
                letter = ({'A', 'B', 'C'} - {first, second}).pop()
                results.append((index + 1, Tower(id[:index] + letter + id[index + 1:])))
                break
        return results

    def get_post(self, index: int) -> str:
        return self.id[index - 1]

    def to_token(self, generator) -> Token:
        return generator.from_tower(self)


def hanoi(disks):
    towers: dict[str, list[int]] = {'A': list(range(disks, 0, -1)), 'B': [], 'C': []}
    result = []

    def move_it(start: str, end: str, state: tuple[str, ...]):
        if start != '':
            value = towers[start].pop()
            towers[end].append(value)
        else:
            value, start, end = 0, ' ', ' '
        tower = Tower.from_stacks(*(tuple(towers[x]) for x in 'ABC'))
        result.append(((value, start, end, state), tower))

    def inner(count: int, start: str, end: str, scratch: str, state: tuple[str, ...]):
        state = (*state, f'S{count}:{start}{end}')
        if count > 0:
            inner(count - 1, start, scratch, end, state)
            move_it(start, end, state)
            inner(count - 1, scratch, end, start, state)

    move_it('', '', ())
    inner(disks, 'A', 'B', 'C', ())
    return result


def half_hanoi(count):
    temp = hanoi(count - 1)
    return [(info, Tower(tower.id + 'A')) for info, tower in temp]


def hamilton(disks, verbose=False):
    towers: dict[str, list[int]] = {'A': list(range(disks, 0, -1)), 'B': [], 'C': []}
    info = {stack: (index, state)
            for index, ((_, _, _, state), stack) in enumerate(half_hanoi(disks), start=1)}
    result = []

    def move_it(start, end, state: tuple[str, ...]):
        if start is not None:
            value = towers[start].pop()
            towers[end].append(value)
        else:
            value, start, end, foo = 0, 0, 0, '   '
        tower = Tower.from_stacks(*(tuple(towers[x]) for x in 'ABC'))
        if tower in info:
            index, state2 = info[tower]
            foo = f'{index:>2} {" ".join(state2)}'
        else:
            foo = ''
        result.append(((value, start, end, state), tower))
        if verbose:
            print(f'<{len(result):>3}: {" ".join(state):<{(disks - 1)*6}} '
                  f'{value}:{start}→{end} {tower} {foo}')

    def outer(count, start, end, scratch, state: tuple[str, ...]):
        state = (*state, f'X{count}:{start}{end}')
        if count >= 1:
            outer(count - 1, start, scratch, end, state)
            move_it(start, end, state)
            # inner(count - 1, scratch, end, start)
            inner(count - 1, scratch, end, start, state),

    def inner(count, start, end, scratch, state):
        state = (*state, f'H{count}:{start}{end}')
        if count >= 1:
            inner(count - 1, start, end, scratch, state)
            move_it(start, scratch, state)
            inner(count - 1, end, start, scratch, state)
            move_it(scratch, end, state)
            inner(count - 1, start, end, scratch, state)

    move_it(None, None, ())
    outer(disks - 1, 'A', 'B', 'C', ())
    return result


def hamilton_hanoi(disks):
    towers: dict[str, list[int]] = {'A': list(range(disks, 0, -1)), 'B': [], 'C': []}
    hanoi = {stack: index for index, (_, stack) in enumerate(half_hanoi(disks), start=1)}
    result = []

    def move_it(start, end, state: bool):
        if start is not None:
            value = towers[start].pop()
            towers[end].append(value)
        else:
            value, start, end, hanoi_info = 0, 0, 0, '   '
        tower = Tower(*(tuple(towers[x]) for x in 'ABC'))
        if tower in hanoi:
            hanoi_info = f'{hanoi[tower]:>2}'
        else:
            hanoi_info = ''
        result.append(((value, start, end, state), tower))
        print(f'{len(result):>3}: {value}:{start}→{end} '
              f'{tower} {hanoi_info} {"*" if state else ""}')

    def outer(count, start, end, scratch):
        """
        This is called only when no moves have yet been made.
        Move to count disks directly from start to end, using scratch as temporary space.
        We are simultaneously figuring out which moves are part of a normal tower of
        Hanoi from scratch -> end
        """
        # 1: 1, odd: 2 + 3x + 2.   even: 2 + 3x + 1
        if count >= 1:
            outer(count - 1, start, scratch, end)
            # 1
            move_it(start, end, True)
            # odd: 3x + 1,  even: 1 + 3x + 2
            inner(count - 1, scratch, end, start, 'normal'),

    def inner(count, start, end, scratch, state: str):
        """
        Move top count disks first from start to scratch and then from scratch to end.
        The "state" indicates which moves are part of the normal tower of Hanoi:
            normal: Mark moves that are part of Hanoi start to end
            leading: Mark moves that are part of Hanoi start to scratch
            trailing: Mark the final move that points all the disks on scratch, and
                then mark the moves that are part of Hanoi scratch to end
            bad: We do not need to track this at allo
        """
        if count >= 1:
            match state:
                case 'normal':
                    # odd: 3x + 1,  even: 1 + 3x + 2
                    state1, move1, state2, move2, state3 = 'leading', False, 'bad', count == 1, 'trailing'
                case 'leading':   # first half
                    # odd: 1 + 3x, even: 3x
                    state1, move1, state2, move2, state3 = 'normal', True, 'leading', False, 'bad'
                case 'trailing':
                    # odd: 3x + 2: even: 3x + 1
                    state1, move1, state2, move2, state3 = 'bad', count == 1, 'trailing', True, 'normal'
                case 'bad':
                    state1, move1, state2, move2, state3 = 'bad', False, 'bad', False, 'bad'
                case _:
                    assert False

            inner(count - 1, start, end, scratch, state1)
            move_it(start, scratch, move1)
            inner(count - 1, end, start, scratch, state2)
            move_it(scratch, end, move2)
            inner(count - 1, start, end, scratch, state3)

    move_it(None, None, True)
    outer(disks - 1, 'A', 'B', 'C')
    return result


def long_path(disks):
    hanoi = [tower for _, tower in half_hanoi(disks)]
    longest_path = [tower for _, tower in hamilton(disks)]
    all_towers = Tower.all_towers(disks)
    graph = {tower.id: set(x.id for _, x in tower.get_neighbors()) for tower in all_towers}

    def verify_paths():
        for tower, neighbors in graph.items():
            for neighbor in neighbors:
                assert tower in graph.get(neighbor, ()), f'{tower}, {neighbor}'

    for tower1, tower2 in itertools.pairwise(hanoi):
        graph[tower1.id].remove(tower2.id)
        graph[tower2.id].remove(tower1.id)

    verify_paths()

    for triangles in range(1, disks):
        good = bad = 0
        for letters in itertools.product('ABC', repeat=disks - triangles):
            base_id = ''.join(letters)
            vertex1, vertex2, vertex3 = vertices = [x + base_id for x in 'ABC']
            if vertex1 in graph and vertex2 in graph and vertex3 in graph:
                path1, path2, path3 = [graph[v] for v in vertices]
                if vertex1 in path2 and vertex1 in path3 and vertex2 in path3:
                    good += 1
                    assert len(path1) + len(path2) + len(path3) == len(path1 | path2 | path3) + 3
                    graph[base_id] = (path1 | path2 | path3) - {vertex1, vertex2, vertex3}
                    for vertex in vertices:
                        del graph[vertex]
                    for vertex in graph[base_id]:
                        graph[vertex].add(base_id)
                        graph[vertex] -= {vertex1, vertex2, vertex3}
                else:
                    bad += 1
        verify_paths()

    def shortest_path(source, dest):
        longest = 0, []
        suffix = next((source[-i:] for i in range(disks, 0, -1) if source[-i:] == dest[-i:]), "")
        heap = [(0, [source])]
        while heap:
            cost, path = heapq.heappop(heap)
            tail = path[-1]
            for neighbor in graph.get(tail):
                if neighbor == dest:
                    longest = cost, path + [neighbor]
                elif neighbor.endswith(suffix) and neighbor not in path:
                    this_cost = 3 ** (disks - len(neighbor))
                    heapq.heappush(heap, (cost + this_cost, path + [neighbor]))
        return longest

    for index in range(3, len(hanoi), 3):
        start = hanoi[index - 1]
        end = hanoi[index]
        delta = longest_path.index(end) - longest_path.index(start)
        print(index, delta, shortest_path(start.id, end.id))


def draw_one(disks):
    import cmath
    import matplotlib.pyplot as plt
    import numpy as np

    direction1 = cmath.exp(complex(0, cmath.pi / 3))
    direction2 = cmath.exp(complex(0, 2 * cmath.pi / 3))

    @cache
    def get_point(tower):
        total = 0
        d1, d2, d3 = 0, direction1, direction2
        for char, index in zip(reversed(tower.id), reversed(range(disks))):
            if char == 'A':
                total += (1 << index) * d1
                d2, d3 = d3, d2
            elif char == 'B':
                total += (1 << index) * d2
                d1, d3 = d3, d1
            else:
                total += (1 << index) * d3
                d1, d2 = d2, d1
        return total

    all_towers = [tower for tower in Tower.all_towers(disks) if tower.id.endswith('A')]
    all_points = np.array([get_point(tower) for tower in all_towers])

    hamilton_towers = [tower for _, tower in hamilton(disks)]
    hamilton_points = np.array([get_point(tower) for tower in hamilton_towers])

    hanoi_towers = [tower for _, tower in half_hanoi(disks)]
    hanoi_points = np.array([get_point(tower) for tower in hanoi_towers])

    _, axes = plt.subplots(1, 1, figsize=(11, 8), dpi=300)
    axes.axis('equal')
    axes.axis([min_x := min(all_points.real), max(all_points.real),
               min(all_points.imag) - .2, max(all_points.imag) + .2]),
    axes.axis('off')


    # Draw in all the joins
    for tower1 in all_towers:
        for _, tower2 in tower1.get_neighbors():
            temp = np.array([get_point(tower1), get_point(tower2)])
            axes.plot(temp.real, temp.imag, color='grey', lw=1, zorder=1)

    plt.plot(hamilton_points.real, hamilton_points.imag, color='red', lw=2, zorder=2)

    plt.scatter(all_points.real, all_points.imag, color='black', marker='.', s=20, zorder=3)

    translator = str.maketrans("ABC", "IPH")
    for tower, point in zip(all_towers, all_points):
        axes.text(point.real, point.imag, str(tower).translate(translator),
                  fontsize=3, fontfamily="sans-serif",
                  fontweight='heavy',
                  rotation=30,
                  va='bottom', ha='left', color='black')

    plt.scatter(all_points.real, all_points.imag, color='black', marker='.', s=20,
                zorder=4)

    plt.plot(hanoi_points.real - .3, hanoi_points.imag, color='green', lw=2)
    plt.text(min_x, 0,
             "Green Path: Orthodox (shortest) Route\n"
             "Red Path: Brother Gregor's Detwoer\n"
             "Gray Lines: Unused path\n"
             "A tag such as IPIPHHH gives the pole\n"
             "    that each of the disks are on from\n"
             "    smallest to largest:\n"
             "  Disks 1 and 3 are on Inundation,\n"
             "  Disks 2 and 4 are on Planting\n"
             "  Disks 5, 6, and 7 are on Harvest",
             va='bottom', ha='left')

    # plt.savefig("/tmp/foo.jpg")
    plt.savefig("/tmp/foo.pdf")

    # plt.show()


if __name__ == '__main__':
    long_path(7)
