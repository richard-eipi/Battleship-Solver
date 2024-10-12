from typing import *
from csp import Constraint, Variable


class AtLeastOneConstraint(Constraint):
    """
    AtLeastOne constraint over a set of variables.
    """

    def __init__(self, name: str, target_variables: Set[Variable], required_value: any):
        Constraint.__init__(self, name, target_variables)
        self._name = "AtLeastOneConstraint_" + name
        self._required_value = required_value

    def is_satisfied(self) -> bool:
        for variable in self.get_target_variables():
            if variable.is_assigned():
                if variable.get_value() == self._required_value:
                    return True
            else:
                return True
        return False

    def has_support(self, variable: Variable, value) -> bool:
        if variable not in self.get_target_variables():
            return True

        if value == self._required_value:
            return True
        else:
            for other_variable in self.get_target_variables():
                if other_variable != variable and other_variable.value_in_curr_domain(self._required_value):
                    return True
            return False


class TableConstraint(Constraint):
    """
    Table constraint over a set of variables.
    """

    def __init__(self, name: str, target_variables: Set[Variable], satisfying_assignments: List[Dict[Variable, any]]):
        Constraint.__init__(self, name, target_variables)
        self._name = "TableConstraint_" + name
        self._satisfying_assignments = satisfying_assignments

    def is_satisfied(self) -> bool:
        assignment = {}
        for variable in self.get_target_variables():
            if variable.is_assigned():
                assignment.update({variable: variable.get_value()})
            else:
                return True

        return assignment in self._satisfying_assignments

    def has_support(self, variable: Variable, value) -> bool:
        if variable not in self.get_target_variables():
            return True

        found_satisfying_assignment = False
        for assignment in self._satisfying_assignments:
            if assignment[variable] != value:
                continue
            found_satisfying_assignment = True
            for other_variable in self.get_target_variables():
                if other_variable != variable and not other_variable.value_in_curr_domain(assignment[other_variable]):
                    found_satisfying_assignment = False
                    break
            if found_satisfying_assignment:
                break

        return found_satisfying_assignment


class NValuesConstraint(Constraint):
    """
    NValues constraint over a set of variables.
    """

    def __init__(self, name: str, target_variables: Set[Variable], required_values: Set[any], lower_bound: int, upper_bound: int):
        Constraint.__init__(self,name, target_variables)
        self._name = "NValuesConstraint_" + name
        self._required_values = required_values
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def is_satisfied(self) -> bool:
        assignments = {}
        for variable in self.get_target_variables():
            if variable.is_assigned():
                assignments.update({variable: variable.get_value()})
            else:
                return True

        required_value_count = 0
        for variable in assignments:
            if assignments[variable] in self._required_values:
                required_value_count += 1

        return self._lower_bound <= required_value_count <= self._upper_bound

    def has_support(self, variable: Variable, value) -> bool:
        if variable not in self.get_target_variables():
            return True

        def check_assignments(assignment: Dict[Variable, any]):
            required_value_count = 0
            for variable in assignment:
                if assignment[variable] in self._required_values:
                    required_value_count += 1
            most = required_value_count + self.get_num_target_variables() - len(assignment)
            least = required_value_count
            return self._lower_bound <= most and self._upper_bound >= least
        variables_to_assign = list(self.get_target_variables())
        variables_to_assign.remove(variable)
        variables_to_assign.sort(reverse=True, key=lambda variable: variable.get_curr_domain_size())
        return self._find_support(variables_to_assign, {variable: value}, check_assignments, check_assignments)

    def _find_support(self, remaining_variables: List[Variable], assignment: Dict[Variable, any], final_test, partial_test) -> bool:
        if len(remaining_variables) == 0:
            return final_test(assignment)
        variable = remaining_variables.pop()  # pop the variable with the smallest domain size
        for value in variable.get_curr_domain():
            assignment.update({variable: value})
            if partial_test(assignment) and self._find_support(remaining_variables, assignment, final_test, partial_test):
                return True
            del assignment[variable]  # this assignment won't work
        remaining_variables.append(variable)
        return False
