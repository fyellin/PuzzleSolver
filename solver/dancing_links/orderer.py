from functools import cache
from typing import Hashable, overload


class _Orderer_LT_LE[T: Hashable]:  # noqa
    @overload
    def __init__(self: _Orderer_LT_LE[int], prefix: str, count: int, is_lt: bool) -> None: ...
    @overload
    def __init__(self, prefix: str, items: set[T], is_lt: bool) -> None: ...

    def __init__(self, prefix: str, count_or_items: int | set[T], is_lt: bool) -> None:
        self._prefix = prefix
        self._is_lt = is_lt
        if isinstance(count_or_items, int):
            self._mapping = None
            count = count_or_items
        else:
            self._mapping = {value: i for i, value in enumerate(sorted(count_or_items))}
            count = len(count_or_items)
        self._count = count
        self._real_count = count + int(is_lt)

    @cache
    def left(self, i: T) -> set[str]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")
        t = int(i) + int(self._is_lt)
        result = set()
        while t > 0:
            result.add(f'{self._prefix}:{t}')
            t &= t - 1
        return result

    @cache
    def right(self, i: T) -> set[str]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")
        t = i + 1
        result = set()
        while t < self._real_count:
            result.add(f'{self._prefix}:{t}')
            t += (t & -t)
        return result

    def all_codes(self) -> set[str]:
        return {f'{self._prefix}:{t}' for t in range(1, self._real_count)}


class OrdererLessEqual[T: Hashable](_Orderer_LT_LE):
    @overload
    def __init__(self: OrdererLessEqual[int], prefix: str, count: int) -> None: ...
    @overload
    def __init__(self, prefix: str, items: set[T]) -> None: ...

    def __init__(self, prefix: str, count_or_items: int | set[T]) -> None:
        super().__init__(prefix, count_or_items, is_lt=False)


class OrdererLessThan[T: Hashable](_Orderer_LT_LE):
    @overload
    def __init__(self: OrdererLessThan[int], prefix: str, count: int) -> None: ...
    @overload
    def __init__(self, prefix: str, items: set[T]) -> None: ...

    def __init__(self, prefix: str, count_or_items: int | set[T]) -> None:
        super().__init__(prefix, count_or_items, is_lt=True)


class OrdererEqual[T: Hashable]:
    @overload
    def __init__(self: OrdererEqual[int], prefix: str, count: int) -> None: ...
    @overload
    def __init__(self, prefix: str, items: set[T]) -> None: ...

    def __init__(self, prefix: str, count_or_items: int | set[T]):
        # We use a single element with coloring.
        self.code = f'{prefix}:0'
        if isinstance(count_or_items, int):
            self._mapping = None
            self._count = count_or_items
        else:
            self._mapping = {value: i for i, value in enumerate(sorted(count_or_items))}
            self._count = len(count_or_items)

    def left(self, i: T) -> set[tuple[str, str]]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")
        return {(self.code, str(i))}

    def right(self, i: int | T) -> set[tuple[str, str]]:
        return self.left(i)

    def all_codes(self) -> set[str]:
        return {self.code}


class Orderer:
    LT = OrdererLessThan
    LE = OrdererLessEqual
    EQ = OrdererEqual
