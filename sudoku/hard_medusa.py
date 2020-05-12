from collections import deque
from typing import Set, Sequence, Dict, Deque, Mapping, Any, Tuple, Optional, ClassVar, Union

from cell import House, CellValue, Cell
from chain import Chain, Chains


class Reason:
    premises: Sequence[CellValue]
    conclusions: Sequence[CellValue]
    cause: Any
    all_reasons: Set['Reason']
    id: int
    
    counter: ClassVar[int] = 0

    def __init__(self, medusa: 'HardMedusa', premises: Sequence[CellValue],
                 conclusions: Sequence[CellValue], cause: Any):
        Reason.counter += 1
        self.id = Reason.counter

        self.all_reasons = {reason for cv in premises for reason in medusa.cell_value_to_reason[cv].all_reasons}
        self.all_reasons.add(self)

        self.premises = premises
        self.conclusions = conclusions
        self.cause = cause

    def is_simpler(self, other: 'Reason') -> bool:
        return len(self.all_reasons) < len(other.all_reasons)

    def simplicity(self) -> int:
        return len(self.all_reasons)

    @staticmethod
    def print_explanations(medusa: 'HardMedusa', cell_values: Set[CellValue]) -> None:
        reasons = {medusa.cell_value_to_reason[cell_value] for cell_value in cell_values}
        Reason.__print_explanations_internal(medusa, reasons)

    def print_explanation(self, medusa: 'HardMedusa'):
        Reason.__print_explanations_internal(medusa, {self})

    @staticmethod
    def __print_explanations_internal(medusa: 'HardMedusa', initial_reasons: Set['Reason']) -> None:
        def print_cell_value(cv: CellValue) -> str:
            chain, group = medusa.chains_mapping[cv]
            truth = medusa.chain_to_true_group[chain] == group
            return cv.to_string(truth)

        all_reasons = {x for reason in initial_reasons for x in reason.all_reasons}
        sorted_reasons = sorted(all_reasons, key=lambda x: x.id)
        line_numbers = {reason: line for line, reason in enumerate(sorted_reasons, start=1)}
        for reason in sorted_reasons:
            line_number = line_numbers[reason]
            print('* ' if reason in initial_reasons else '  ', end='')
            print(f'{line_number:3}: ', end='')
            result = []
            for cell_value in sorted(reason.premises):
                super_reason = medusa.cell_value_to_reason[cell_value]
                super_line_number = line_numbers[super_reason]
                result.append(f'{print_cell_value(cell_value)}({super_line_number})')
            print(', '.join(result), end='')
            print(' ⇒ ', end='')
            if reason.cause:
                print(reason.cause, end=' ')
            print('{', end='')
            print(', '.join(print_cell_value(cell_value) for cell_value in sorted(reason.conclusions)), end='')
            print('}')

    def __repr__(self) -> str:
        return f'<Reason #{self.id} length {len(self.all_reasons)}>'


class HardMedusa:
    chains_mapping: Mapping[CellValue, Tuple[Chain, Chain.Group]]
    true_values: Set[CellValue]
    false_values: Set[CellValue]
    chain_to_true_group: Dict[Chain, Chain.Group]
    cell_value_to_reason: Dict[CellValue, Reason]

    todo: Deque[CellValue]

    @staticmethod
    def run(chains: Chains) -> bool:
        for chain in chains.chains:
            medusa1 = HardMedusa(chains.mapping)
            medusa2 = HardMedusa(chains.mapping)
            contradiction1 = medusa1.__find_contradictions(chain, Chain.Group.ONE)
            contradiction2 = medusa2.__find_contradictions(chain, Chain.Group.TWO)
            assert not(contradiction1 and contradiction2)
            if contradiction1 or contradiction2:
                contradiction, group, medusa = (contradiction1, Chain.Group.ONE, medusa1) if contradiction1 is not None else (contradiction2, Chain.Group.TWO, medusa2)
                print(f"Setting strong chain {chain} to {group.marker()} yields contradiction")
                contradiction.print_explanation(medusa)
                chain.set_true(group.other())
                return True
            elif contradiction2:
                print(f"Setting strong chain {chain} to {Chain.Group.TWO.marker()} yields contradiction")
                # Group.TWO leads to a contradiction
                contradiction2.print_explanation(medusa2)
                chain.set_true(Chain.Group.ONE)
                return True
            else:
                joint_trues = medusa1.true_values.intersection(medusa2.true_values)
                joint_falses = medusa1.false_values.intersection(medusa2.false_values)
                all_values = joint_trues.union(joint_falses)
                if joint_trues or joint_falses:
                    print(f"Setting value of {chain} to either {Chain.Group.ONE.marker()} "
                          f"or {Chain.Group.TWO.marker()} yields common results")
                    print(f'{Chain.Group.ONE.marker()}. . . ')
                    Reason.print_explanations(medusa1, all_values)
                    print(f'{Chain.Group.TWO.marker()}. . . ')
                    Reason.print_explanations(medusa2, all_values)
                    for (cell, value) in joint_falses:
                        Cell.remove_value_from_cells({cell}, value)
                    for (cell, value) in joint_trues:
                        cell.set_value_to(value, show=True)
                    return True
        return False

    def __init__(self, cell_value_to_chain: Mapping[CellValue, Tuple[Chain, Chain.Group]]):
        self.chains_mapping = cell_value_to_chain

    def __find_contradictions(self, chain: Chain, group: Chain.Group) -> Optional[Reason]:
        self.true_values = set()
        self.false_values = set()
        self.chain_to_true_group = {}
        self.todo = deque()
        self.cell_value_to_reason = {}

        self.__set_chain_group_to_true(chain, group)

        contradiction: Optional[Reason] = None

        while self.todo:
            cell_value = self.todo.popleft()
            if contradiction is not None and contradiction.is_simpler(self.cell_value_to_reason[cell_value]):
                continue
            assert cell_value in self.false_values or cell_value in self.true_values
            assert not(cell_value in self.false_values and cell_value in self.true_values)
            if cell_value in self.false_values:
                temp = self.__handle_cell_value_false(cell_value)
            else:
                temp = self.__handle_cell_value_true(cell_value)
            if temp is not None and (contradiction is None or temp.is_simpler(contradiction)):
                contradiction = temp
        return contradiction

    def __handle_cell_value_true(self, cell_value: CellValue) -> Optional[Reason]:
        this_cell, this_value = cell_value
        falsehoods: Set[CellValue] = set()
        falsehoods.update(CellValue(cell, this_value) for cell in this_cell.neighbors
                          if cell.known_value is None
                          if this_value in cell.possible_values)
        falsehoods.update(CellValue(this_cell, value) for value in this_cell.possible_values
                          if value != this_value)

        contradictions = {x for x in falsehoods if x in self.true_values}
        if contradictions:
            simplest_truth = min(contradictions, key=lambda x: self.cell_value_to_reason[x].simplicity())
            return Reason(self, (cell_value, simplest_truth), (), "Contradiction")

        final_list = [x for x in falsehoods if x not in self.false_values]
        if final_list:
            self.__set_values([cell_value], final_list, False, None)
        return None

    def __handle_cell_value_false(self, cell_value: CellValue) -> Optional[Reason]:
        this_cell, this_value = cell_value
        probes = [CellValue(this_cell, value) for value in this_cell.possible_values]
        result = self.__check_if_one_is_true(probes, cell_value.cell)
        if result:
            return result

        for house_type in House.Type:
            house = this_cell.house_of_type(house_type)
            probes = [CellValue(cell, this_value)
                      for cell in house.unknown_cells
                      if this_value in cell.possible_values]
            result = self.__check_if_one_is_true(probes, house)
            if result:
                return result
        return None

    def __check_if_one_is_true(self, probes: Sequence[CellValue], cause: Union[Cell, House]) -> Optional[Reason]:
        if any(x in self.true_values for x in probes):
            # We've already got one that's true.  We're fine
            return None
        possibilities = [x for x in probes if x not in self.false_values]
        if len(possibilities) == 0:
            # There is nothing we can set to true.  We have a contradiction
            return Reason(self, probes, (), f'No value for {cause}')

        if len(possibilities) == 1:
            possibility = possibilities[0]
            # There is only one thing we can to true.  Go ahead and do it.
            causes = [cv for cv in probes if cv != possibility]
            self.__set_values(causes, (possibility,), True, cause)
        return None

    def __set_values(self, premises: Sequence[CellValue],
                     cell_values: Sequence[CellValue], truthhood: bool, cause: Any) -> None:
        reason = Reason(self, premises, cell_values, cause)
        for cell_value in cell_values:
            # Find which chain and which Group of that chain we belong to.
            chain, group = self.chains_mapping[cell_value]
            # Which clue group is being set to True, us or the other group.
            true_group = group if truthhood else group.other()
            if chain in self.chain_to_true_group:
                # Has this chain already been assigned a value?  Make sure we set it to the
                assert true_group == self.chain_to_true_group[chain]
                continue
            self.__set_chain_group_to_true(chain, true_group, reason, cell_value)

    def __set_chain_group_to_true(self, chain: Chain, group: Chain.Group, 
                                  reason: Optional[Reason] = None, cell_value: Optional[CellValue] = None):
        self.chain_to_true_group[chain] = group
        true_values = group.pick_set(chain)
        false_values = group.pick_other_set(chain)
        all_values = list(true_values) + list(false_values)
        self.true_values.update(true_values)
        self.false_values.update(false_values)
        self.todo.extend(all_values)
        if not reason:
            assert cell_value is None
            reason = Reason(self, (), all_values, 'BASIS')
            self.cell_value_to_reason.update((cv, reason) for cv in all_values)
        else:
            assert cell_value is not None
            assert cell_value in all_values
            self.cell_value_to_reason[cell_value] = reason
            all_values.remove(cell_value)
            if all_values:
                assert len(all_values) == len(chain) - 1
                sub_reason = Reason(self, (cell_value,), all_values, "STRONG CHAIN")
                self.cell_value_to_reason.update((cv, sub_reason) for cv in all_values)
        assert len(self.cell_value_to_reason) == len(self.false_values) + len(self.true_values)
