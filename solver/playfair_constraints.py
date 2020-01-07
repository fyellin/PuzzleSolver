import itertools
from typing import Dict, Tuple, Set, FrozenSet, Optional, Sequence, Any


class ConstraintsGenerator:
    # For each pair of letters AB in the plaintext, where we know that AB encrypts to CD (hereafter written AB->CD),
    # we generate a constraint.  A constraint is a set of Rows, where each row indicates a possible location of A, B
    # C, and D.  We have a solution when we've picked one row from each constraint this are mutually consistent.
    def __init__(self, plain_text: str="", cipher_text: str=""):
        self.plain_text = plain_text
        assert len(plain_text) == len(cipher_text)
        assert len(plain_text) % 2 == 0
        self.cipher_text = cipher_text

    def generate_all_constraints(self) -> Dict[str, Sequence['ConstraintRow']]:
        """
        Generate all constraints for the given plain_text / cipher_text pair.  For now, we only do constraints
        that list all possible solutions of AB->CD, but others may be possible in the future.
        """
        return self.generate_encryption_constraints()

    def generate_encryption_constraints(self) -> Dict[str, Sequence['ConstraintRow']]:
        """
        Generates the encryption constraints.  The cipher text and plain text are broken down into pairs of letters,
        and a constraint is generated for each pair.
        """
        result = {}
        for i in range(0, len(self.plain_text), 2):
            constraints = self.generate_one_encryption_constraint(
                self.plain_text[i], self.plain_text[i + 1], self.cipher_text[i], self.cipher_text[i + 1])
            if constraints:
                result["{}:{}".format(i, i + 2)] = constraints
        return result

    @staticmethod
    def generate_one_encryption_constraint(p0: str, p1: str, c0: str, c1: str) -> Optional[Sequence['ConstraintRow']]:
        if p0 == '.' and p1 == '.':
            return None
        if c0 == '.' and c1 == '.':
            return None
        # Verify the fact that we can't encrypt or decrypt double letters
        assert p0 != p1 and c0 != c1
        # Verify the fact that no letter encrypts or decrypts to itself
        assert (p0 == '.' or p0 != c0) and (p1 == '.' or p1 != c1)
        result = []
        seen: Set['ConstraintRow'] = set()
        # Look at ever possible pair of positions for p0 and p1.
        for (row0, column0, row1, column1) in itertools.product(range(5), repeat=4):
            if (row0, column0) == (row1, column1):
                continue
            # We use a set.  It's okay for a letter to be added twice, as long as it's at the same position
            # both times.  Likewise, it's okay for a position to be used twice, as long as the same letter is put
            # there both times.  We use a set for letter_positions to eliminate duplicates
            letter_positions = {(p0, (row0, column0)), (p1, (row1, column1))}
            if row0 == row1:
                letter_positions.add((c0, (row0, (column0 + 1) % 5)))
                letter_positions.add((c1, (row0, (column1 + 1) % 5)))
            elif column0 == column1:
                letter_positions.add((c0, ((row0 + 1) % 5, column0)))
                letter_positions.add((c1, ((row1 + 1) % 5, column0)))
            else:
                letter_positions.add((c0, (row0, column1)))
                letter_positions.add((c1, (row1, column0)))
            # Remove everything we've added that's actually just a blank
            letter_positions = {(letter, location) for (letter, location) in letter_positions if letter != "."}
            # No letter should be in two positions, and no position should have two different letters
            if len(set(letter for letter, _ in letter_positions)) != len(letter_positions):
                continue
            if len(set(location for _, location in letter_positions)) != len(letter_positions):
                continue
            # We've got a nice, consistent result.  Turn it into a constraint.
            constraint_row = ConstraintRow({letter: position for letter, position in letter_positions})
            # We may have duplicates if more than one of p0, p1, c0, c1 is blank.  We keep track of seen results to
            # avoid adding duplicates.
            if constraint_row not in seen:
                result.append(constraint_row)
                seen.add(constraint_row)
        return result


class ConstraintRow (object):
    _locations: FrozenSet[Tuple[int, int]]
    _letter_to_location: Dict[str, Tuple[int, int]]
    _tuple: Tuple[str, ...]

    def __init__(self, location_dict: Dict[str, Tuple[int, int]]):
        self._letter_to_location = location_dict
        self._locations = frozenset(location_dict.values())
        array = ['.'] * 25
        for letter, (row, column) in location_dict.items():
            array[5 * row + column] = letter
        self._tuple = tuple(array)

    @staticmethod
    def empty() -> 'ConstraintRow':
        return ConstraintRow({})

    @staticmethod
    def from_string(string: Sequence[str]) -> 'ConstraintRow':
        all_positions = [(string[row * 5 + column], (row, column)) for row in range(5) for column in range(5)]
        location_dict = {letter: location for letter, location in all_positions if letter != '.'}
        return ConstraintRow(location_dict)

    def __repr__(self) -> str:
        array = ['.'] * 29
        for i in range(5, len(array), 6):
            array[i] = '|'
        for letter, (row, column) in self._letter_to_location.items():
            array[6 * row + column] = letter
        return ''.join(array)

    def is_consistent_with(self, other: 'ConstraintRow') -> bool:
        """
        Returns True if self doesn't conflict with other.
        If both have any letters in common, they are both in the same location.  If both have any locations in
        common, they both have the same letter.
        """
        for letter, location in self._letter_to_location.items():
            other_location = other._letter_to_location.get(letter, None)
            if not other_location:
                if location in other._locations:
                    return False
            else:
                if location != other_location:
                    return False
        return True

    # noinspection SpellCheckingInspection
    ALL_LETTERS = frozenset("ABCDEFGHIKLMNOPQRSTUVWXYZ")

    def missing_letters(self) -> Set[str]:
        return set(self.ALL_LETTERS).difference(list(self._letter_to_location.keys()))

    def fill_in_tail(self, sorted_tail_length: int) -> Optional['ConstraintRow']:
        string = list(self._tuple)
        unused_letters = self.missing_letters()

        # We start off by pretending that the spot just before the tail is filled with a character smaller than 'A'
        last_filled_index = len(string) - sorted_tail_length - 1
        last_filled_value = chr(ord('A') - 1)

        while last_filled_index < len(string):
            # Look for the next filled spot.  If there is none, create a fake one just beyond the end of the string
            next_filled_index = next(
                (i for i in range(last_filled_index + 1, len(string)) if string[i] != '.'),
                len(string))
            next_filled_value = string[next_filled_index] if next_filled_index < len(string) else chr(ord('Z') + 1)
            # The next character should always be greater than the current one.  Otherwise, this has failed.
            if next_filled_value <= last_filled_value:
                return None
            # Are there spots between the last filled character and this one?  If so, try to fill them.
            unfilled_spots = next_filled_index - last_filled_index - 1
            if unfilled_spots != 0:
                candidates = [x for x in unused_letters if last_filled_value < x < next_filled_value]
                if len(candidates) < unfilled_spots:
                    return None
                if len(candidates) == unfilled_spots:
                    # We have exactly the right number of candidates for the unfilled spots.  Fill them in
                    string[last_filled_index + 1:next_filled_index] = sorted(candidates)
                    unused_letters.difference_update(candidates)
            last_filled_index = next_filled_index
            last_filled_value = next_filled_value
        if len(unused_letters) == 1:
            # If we have exactly one unused letter left, there must be an unfilled spot in the string for it.
            string[string.index('.')] = unused_letters.pop()
        return ConstraintRow.from_string(string)

    def __hash__(self) -> int:
        return hash(self._tuple)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ConstraintRow):
            return NotImplemented
        return self._tuple == other._tuple

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, ConstraintRow):
            return NotImplemented
        return self._tuple != other._tuple

    def __add__(self, other: 'ConstraintRow') -> 'ConstraintRow':
        letter_to_location = {}
        letter_to_location.update(self._letter_to_location)
        letter_to_location.update(other._letter_to_location)
        return ConstraintRow(letter_to_location)
