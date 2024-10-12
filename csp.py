from typing import *
from abc import abstractmethod


class Variable:
    """
    Class for defining CSP variables.
    """
    undo_dict = dict()

    def __init__(self, name: any, domain: set):
        self._name = name
        self._domain = domain
        self._value = None
        self._curr_domain = domain.copy()

    def get_name(self) -> any:
        return self._name

    def get_domain(self) -> set:
        return self._domain

    def get_domain_size(self) -> int:
        return len(self._domain)

    def get_value(self):
        return self._value

    def set_value(self, value) -> None:
        assert value in self._domain
        self._value = value

    def unassign(self) -> None:
        self._value = None

    def is_assigned(self) -> bool:
        return self._value is not None

    def get_curr_domain(self) -> set:
        if self.is_assigned():
            return {self.get_value()}
        else:
            return self._curr_domain

    def get_curr_domain_size(self) -> int:
        if self.is_assigned():
            return 1
        return len(self._curr_domain)

    def value_in_curr_domain(self, value) -> bool:
        if self.is_assigned():
            return value == self.get_value()
        return value in self._curr_domain

    def remove_value_from_curr_domain(self, value, reason_variable, reason_value) -> None:
        assert value in self._curr_domain
        self._curr_domain.remove(value)
        key = (reason_variable, reason_value)
        if key not in Variable.undo_dict:
            Variable.undo_dict[key] = []
        Variable.undo_dict[key].append((self, value))

    def restore_value(self, value) -> None:
        self._curr_domain.add(value)

    def restore_curr_domain(self) -> None:
        self._curr_domain = self._domain

    def reset(self) -> None:
        self.restore_curr_domain()
        self.unassign()

    def print_variable(self):
        print("Variable\"{} = {}\": Dom = {}, CurDom = {}".format(self._name, self._value, self._domain, self._curr_domain))

    @staticmethod
    def clear_undo_dict():
        Variable.undo_dict = dict()

    @staticmethod
    def restore_values(reason_variable, reason_value):
        key = (reason_variable, reason_value)
        if key in Variable.undo_dict:
            for (variable, value) in Variable.undo_dict[key]:
                variable.restore_value(value)
            del Variable.undo_dict[key]


class Constraint:
    """
    Parent class for defining CSP constraints.
    """

    def __init__(self, name: str, target_variables: Set[Variable]):
        self._target_variables = target_variables
        self._name = "generic_constraint_" + name  # override in subconstraint types!

    def get_name(self) -> str:
        return self._name

    def get_target_variables(self) -> Set[Variable]:
        return self._target_variables

    def get_num_target_variables(self) -> int:
        return len(self._target_variables)

    def get_unassigned_variables(self):
        return [variable for variable in self._target_variables if not variable.is_assigned()]

    def get_num_unassigned_variables(self) -> int:
        i = 0
        for var in self._target_variables:
            if not var.is_assigned():
                i += 1
        return i

    def print_constraint(self):
        print("Constraint: {} Variables = {}".format(self._name, [v.get_name() for v in self._target_variables]))

    @abstractmethod
    def is_satisfied(self) -> bool:
        pass

    @abstractmethod
    def has_support(self, variable: Variable, value) -> bool:
        pass


class CSP:
    """
    CSP class.
    """

    def __init__(self, name: str, variables: Set[Variable], constraints: Set[Constraint]):
        self._name = name
        self._variables = variables
        self._constraints = constraints

        # Know which constraints each variable is involved in
        self._constraints_of_each_variable = {variable: set() for variable in variables}
        for constraint in constraints:
            for variable in constraint.get_target_variables():
                self._constraints_of_each_variable[variable].add(constraint)

        # Make sure constraints do not use out-of-scope variables
        variables_in_constraints = set()
        for constraint in constraints:
            variables_in_constraints = variables_in_constraints.union(constraint.get_target_variables())
        for variable in variables:
            if variable not in variables_in_constraints:
                print("Warning: variable {} is not in any constraint of the CSP {}".format(variable.get_name(), self._name))
        for variable in variables_in_constraints:
            assert variable in variables

    def get_name(self) -> str:
        return self._name

    def get_variables(self) -> Set[Variable]:
        return self._variables

    def get_constraints(self) -> Set[Constraint]:
        return self._constraints

    def get_constraints_of_variable(self, variable: Variable) -> Set[Constraint]:
        assert variable in self._variables
        return self._constraints_of_each_variable[variable]

    def unassign_all_variables(self) -> None:
        for variable in self._variables:
            variable.unassign()
