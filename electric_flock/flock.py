"""
Sheep collection management
"""
from collections import defaultdict
from collections.abc import Iterable, Iterator, MutableSet
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True, weakref_slot=True)
class Sheep:
    """
    An individual video segment
    """
    path: Path = field(compare=False)
    gen: int = field(compare=True)
    ident: int = field(compare=True)
    start: int = field(compare=False)
    end: int = field(compare=False)
    # All sheep seem to be 5 seconds?
    length: int = field(default=5, compare=False)

    @property
    def is_loop(self) -> bool:
        return self.ident == self.start == self.end

    @classmethod
    def from_path(cls, path: Path | str | PathLike) -> Self:
        path = Path(path).absolute()
        return cls(path, *map(int, path.stem.split('=')))


Sheepish = Sheep | tuple[int, int]


class Flock(MutableSet[Sheep]):
    """
    A collection of sheep, with a bunch of handy lookups
    """
    _sheep: set[Sheep]
    _idents: dict[tuple[int, int], Sheep]
    _nexts: dict[tuple[int, int], set[Sheep]]

    def __init__(self, iterable=()):
        self._sheep = set(iterable)
        self._idents = {(s.gen, s.ident): s for s in self._sheep}
        self._nexts = defaultdict(set)
        for s in self._sheep:
            self._nexts[s.gen, s.start].add(s)

    def __contains__(self, item: Sheep) -> bool:
        return item in self._sheep

    def __iter__(self) -> Iterator[Sheep]:
        yield from self._sheep

    def __len__(self) -> int:
        return len(self._sheep)

    def add(self, item: Sheep | PathLike):
        if not isinstance(item, Sheep):
            # Assume PathLike
            item = Sheep.from_path(item)
        self._sheep.add(item)
        self._idents[item.gen, item.ident] = item
        self._nexts[item.gen, item.start].add(item)

    def update(self, items: Iterable[Sheep | PathLike]):
        for item in items:
            self.add(item)

    def discard(self, item: Sheep):
        self._sheep.discard(item)
        del self._idents[item.gen, item.ident]
        del self._nexts[item.gen, item.ident]
        for nexts in self._nexts.values():
            nexts.discard(item)

    def discard_missing(self):
        """
        Scans the flock and removes sheep that no longer exist on the 
        filesystem.
        """
        for sheep in self._sheep:
            if not sheep.path.exists():
                self.discard(sheep)

    def __getitem__(self, key: tuple[int, int]) -> Sheep:
        return self._idents[key]

    def find_next_sheep(self, item: Sheepish) -> Iterable[Sheep]:
        """
        Given a sheep, find the sheep that can follow it.
        """
        if isinstance(item, Sheep):
            item = item.gen, item.ident
        yield from self._nexts[item]
