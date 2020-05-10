from collections import deque
from typing import Set, Sequence, Dict, Deque, Iterable, Mapping, Any, Tuple, Optional

from cell import House, CellValue
from chain import Chain


class Reason:
    medusa: 'HardMedusa'
    premises: Set[CellValue]
    conclusions: Set[CellValue]
    cause: Any
    all_reasons: Set['Reason']
    id: int
    
    counter: int = 0

    def __init__(self, medusa: 'HardMedusa', premises: Set[CellValue], conclusions: Set[CellValue], cause: Any):
        Reason.counter += 1
        self.id = Reason.counter

        self.all_reasons = {reason for cv in premises for reason in medusa.cell_value_to_reason[cv].all_reasons}
        self.all_reasons.add(self)

        self.medusa = medusa
        self.premises = premises
        self.conclusions = conclusions
        self.cause = cause

    def is_simpler(self, other: 'Reason') -> bool:
        return len(self.all_reasons) < len(other.all_reasons)

    def simplicity(self):
        return len(self.all_reasons)

    def print_cell_value(self, cv: CellValue) -> str:
        chain, group = self.medusa.cell_value_to_chain[cv]
        truth = self.medusa.chain_to_true_group[chain] == group
        return cv.to_string(truth)

    def print_contradiction(self) -> None:
        sorted_reasons = sorted(self.all_reasons, key=lambda x: x.id)
        line_numbers = { reason: line for line, reason in enumerate(sorted_reasons, start=1)}
        for reason in sorted_reasons:
            line_number = line_numbers[reason]
            print(f'{line_number:3}: ', end='')
            result = []
            for cell_value in sorted(reason.premises):
                super_reason = self.medusa.cell_value_to_reason[cell_value]
                super_line_number = line_numbers[super_reason]
                result.append(f'{self.print_cell_value(cell_value)}({super_line_number})')
            print(', '.join(result), end='')
            print(' ⇒ ', end='')
            if reason.cause:
                print(reason.cause, end=' ')
            print('{', end='')
            print(', '.join(self.print_cell_value(cell_value) for cell_value in sorted(reason.conclusions)), end='')
            print('}')

    def __repr__(self) -> str:
        return f'<Reason #{self.id} length {len(self.all_reasons)}>'


class HardMedusa:
    cell_value_to_chain: Mapping[CellValue, Tuple[Chain, Chain.Group]]
    true_values: Set[CellValue]
    false_values: Set[CellValue]
    chain_to_true_group: Dict[Chain, Chain.Group]
    todo: Deque[CellValue]
    contradiction: bool

    cell_value_to_reason: Dict[CellValue, Reason]

    @staticmethod
    def run(chains: Sequence[Chain]) -> bool:
        cell_value_to_chain = {cell_value: (chain, group) for chain in chains for cell_value, group in chain.items()}
        for chain in chains:
            medusa1 = HardMedusa(cell_value_to_chain)
            medusa2 = HardMedusa(cell_value_to_chain)
            contradiction1 = medusa1.__find_contradictions(chain, Chain.Group.ONE)
            contradiction2 = medusa2.__find_contradictions(chain, Chain.Group.TWO)
            if contradiction1 and contradiction2:
                assert False
            if contradiction1 and not contradiction2:
                # Group.ONE leads to a contradiction
                contradiction1.print_contradiction()
                chain.set_true(Chain.Group.TWO)
                return True
            elif contradiction2 and not contradiction1:
                # Group.TWO leads to a contradiction
                contradiction2.print_contradiction()
                chain.set_true(Chain.Group.ONE)
                return True
            else:
                joint_trues = medusa1.true_values.intersection(medusa2.true_values)
                joint_falses = medusa1.false_values.intersection(medusa2.false_values)
                if joint_trues or joint_falses:
                    print(f'Strong chain {chain.to_string(Chain.Group.ONE)} and converse yield same result')
                    for (cell, value) in joint_falses:
                        cell.possible_values.remove(value)
                        print(f'  {cell} ≠ {value} -> {cell.possible_value_string()}')
                    for (cell, value) in joint_trues:
                        cell.set_value_to(value)
                        print(f'  {cell} := {value}')
                    return True
        return False

    def __init__(self, cell_value_to_chain: Mapping[CellValue, Tuple[Chain, Chain.Group]]):
        self.cell_value_to_chain = cell_value_to_chain

    def __find_contradictions(self, chain: Chain, group: Chain.Group) -> Optional[Reason]:
        self.true_values = set()
        self.false_values = set()
        self.chain_to_true_group = {}
        self.todo = deque()
        self.cell_value_to_reason = {}

        self.__set_chain_group_to_true(chain, group)

        contradiction: Optional[Reason] = None

        while self.todo and contradiction is None:
            clue_value = self.todo.popleft()
            assert clue_value in self.false_values or clue_value in self.true_values
            assert not(clue_value in self.false_values and clue_value in self.true_values)
            if clue_value in self.false_values:
                contradiction = self.__handle_cell_value_false(clue_value)
            else:
                contradiction = self.__handle_cell_value_true(clue_value)
        return contradiction

    def __handle_cell_value_true(self, cell_value: CellValue) -> Optional[Reason]:
        this_cell, this_value = cell_value
        falsehoods = set()
        falsehoods.update(CellValue(cell, this_value) for cell in this_cell.neighbors
                          if cell.known_value is None
                          if this_value in cell.possible_values)
        falsehoods.update(CellValue(this_cell, value) for value in this_cell.possible_values
                          if value != this_value)

        contradictions = {x for x in falsehoods if x in self.true_values}
        if contradictions:
            simplest_truth = min(contradictions, key=lambda x: self.cell_value_to_reason[x].simplicity())
            return Reason(self, {cell_value, simplest_truth}, set(), "Contradiction")

        final_list = [x for x in falsehoods if x not in self.false_values]
        if final_list:
            self.__set_values([cell_value], final_list, False, None)
        return None

    def __handle_cell_value_false(self, cell_value: CellValue) -> Optional[Reason]:
        this_cell, this_value = cell_value
        probes = [CellValue(this_cell, value) for value in this_cell.possible_values]
        if result := self.__check_if_one_is_true(probes, cell_value):
            return result

        for house_type in House.Type:
            house = this_cell.house_of_type(house_type)
            probes = [CellValue(cell, this_value)
                      for cell in house.unknown_cells
                      if this_value in cell.possible_values]
            if result := self.__check_if_one_is_true(probes, house):
                return result
        return None

    def __check_if_one_is_true(self, probes: Sequence[CellValue], cause: Any) -> Optional[Reason]:
        if any(x in self.true_values for x in probes):
            # We've already got one that's true.  We're fine
            return None
        possibilities = [x for x in probes if x not in self.false_values]
        if len(possibilities) == 0:
            # There is nothing we can set to true.  We have a contradiction
            return Reason(self, set(probes), set(), "Contradiction")

        if len(possibilities) == 1:
            # There is only one thing we can to true.  Go ahead and do it.
            causes = set(probes).difference(possibilities)
            self.__set_values(causes, possibilities, True, cause)
        return None

    def __set_values(self, premises: Iterable[CellValue],
                     cell_values: Iterable[CellValue], truthhood: bool, cause: Any) -> None:
        for cell_value in cell_values:
            # Find which chain and which Group of that chain we belong to.
            chain, group = self.cell_value_to_chain[cell_value]
            # Which clue group is being set to True, us or the other group.
            true_group = group if truthhood else group.other()
            if chain in self.chain_to_true_group:
                # Has this chain already been assigned a value?  Make sure we set it to the
                assert true_group == self.chain_to_true_group[chain]
                continue
            reason = Reason(self, set(premises), set(cell_values), cause)
            self.__set_chain_group_to_true(chain, true_group, reason, cell_value)

    def __set_chain_group_to_true(self, chain: Chain, group: Chain.Group, 
                                  reason: Optional[Reason] = None, cell_value: Optional[CellValue] = None):
        self.chain_to_true_group[chain] = group
        true_values = group.pick_set(chain)
        false_values = group.pick_other_set(chain)
        all_values = set(true_values).union(false_values)
        self.true_values.update(true_values)
        self.false_values.update(false_values)
        self.todo.extend(all_values)
        if not reason:
            assert cell_value is None
            reason = Reason(self, set(), all_values, 'BASIS')
            self.cell_value_to_reason.update((cv, reason) for cv in all_values)
        else:
            assert cell_value is not None
            assert cell_value in all_values
            all_values.remove(cell_value)
            self.cell_value_to_reason[cell_value] = reason
            if all_values:
                sub_reason = Reason(self, {cell_value}, all_values, "STRONG CHAIN")
                self.cell_value_to_reason.update((cv, sub_reason) for cv in all_values)
        temp1 = set(self.cell_value_to_reason.keys())
        temp2 = self.true_values.union(self.false_values)
        assert temp1 == temp2

