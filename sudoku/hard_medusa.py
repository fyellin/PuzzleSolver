from collections import deque
from typing import Set, Sequence, Dict, Deque, Iterable, Mapping

from cell import House, CellValue
from chain import Chain


class HardMedusa:
    cv_to_chain_map: Mapping[CellValue, Chain]
    true_values: Set[CellValue]
    false_values: Set[CellValue]
    chain_groups: Dict[Chain, Chain.Group]
    todo: Deque[CellValue]
    contradiction: bool

    @staticmethod
    def run(chains: Sequence[Chain]) -> bool:
        chain_map = {cell_value: chain for chain in chains
                     for cell_values in (chain.one, chain.two) for cell_value in cell_values}
        for chain in chains:
            medusa1 = HardMedusa(chain_map)
            medusa2 = HardMedusa(chain_map)
            contradiction1 = medusa1.__find_contradictions(chain, Chain.Group.ONE)
            contradiction2 = medusa2.__find_contradictions(chain, Chain.Group.TWO)
            if contradiction1 and contradiction2:
                assert False
            if contradiction1 and not contradiction2:
                # Group.ONE leads to a contradiction
                chain.set_true(Chain.Group.TWO)
                return True
            elif contradiction2 and not contradiction1:
                # Group.TWO leads to a contradiction
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

    def __init__(self, cv_to_chain_map: Mapping[CellValue, Chain]):
        self.cv_to_chain_map = cv_to_chain_map

    def __find_contradictions(self, chain: Chain, group: Chain.Group):
        self.true_values = set()
        self.false_values = set()
        self.chain_groups = {}
        self.todo = deque()

        self.__set_chain_group_to_true(chain, group)

        contradiction = False

        while self.todo and not contradiction:
            clue_value = self.todo.popleft()
            assert clue_value in self.false_values or clue_value in self.true_values
            assert not(clue_value in self.false_values and clue_value in self.true_values)
            if clue_value in self.false_values:
                contradiction = self.__handle_cell_value_false(clue_value)
            else:
                contradiction = self.__handle_cell_value_true(clue_value)
        return contradiction


    def __handle_cell_value_true(self, cell_value: CellValue) -> bool:
        this_cell, this_value = cell_value
        falsehoods = set()
        falsehoods.update(CellValue(cell, this_value) for cell in this_cell.neighbors
                          if cell.known_value is None
                          if this_value in cell.possible_values)
        falsehoods.update(CellValue(this_cell, value) for value in this_cell.possible_values
                          if value != this_value)

        if any(x in self.true_values for x in falsehoods):
            return True
        final_list = [x for x in falsehoods if x not in self.false_values]
        if final_list:
            self.__set_values(final_list, False)
        return False

    def __handle_cell_value_false(self, cell_value: CellValue) -> bool:
        this_cell, this_value = cell_value
        probes = [CellValue(this_cell, value) for value in this_cell.possible_values]
        if self.__check_if_one_is_true(probes):
            return True

        for house_type in House.Type:
            house = this_cell.house_of_type(house_type)
            probes = [CellValue(cell, this_value)
                      for cell in house.unknown_cells
                      if this_value in cell.possible_values]
            if self.__check_if_one_is_true(probes):
                return True
        return False

    def __check_if_one_is_true(self, probes: Sequence[CellValue]) -> bool:
        if any(x in self.true_values for x in probes):
            # We've already got one that's true.  We're fine
            return False
        possibilities = [x for x in probes if x not in self.false_values]
        if len(possibilities) == 0:
            # There is nothing we can set to true.  We have a contradiction
            return True

        if len(possibilities) == 1:
            # There is only one thing we can to true.  Go ahead and do it.
            self.__set_values(possibilities, True)
        return False

    def __set_values(self, cell_values: Iterable[CellValue], truthhood: bool) -> None:
        for cell_value in cell_values:
            # Find which chain and which Group of that chain we belong to.
            chain = self.cv_to_chain_map[cell_value]
            cell_value_group = chain.get_group(cell_value)
            # Which clue group is being set to True, us or the other group.
            true_group = cell_value_group if truthhood else cell_value_group.other()
            if chain in self.chain_groups:
                # Has this chain already been assigned a value?  Make sure we set it to the
                assert true_group == self.chain_groups[chain]
            else:
                self.__set_chain_group_to_true(chain, true_group)

    def __set_chain_group_to_true(self, chain: Chain, group: Chain.Group):
        self.chain_groups[chain] = group
        trues = group.pick_set(chain)
        falses = group.pick_other_set(chain)
        self.true_values.update(trues)
        self.false_values.update(falses)
        self.todo.extend(trues)
        self.todo.extend(falses)
