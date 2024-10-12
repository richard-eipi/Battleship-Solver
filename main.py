import argparse
import math
from csp import *
from constraints import *


ship_parts = {'S', '<', '>', '^', 'v', 'M'}


#====================================================================================


def find_solutions(csp: CSP, initial_assignments: Dict[Variable, any]) -> List[Dict[Tuple[int, int], any]]:
    # Preprocessing
    for variable in initial_assignments:
        assert reduce_domains(csp, variable, initial_assignments[variable])
    new_assignments = {}
    for variable in csp.get_variables():
        if not variable.is_assigned() and variable.get_curr_domain_size() == 1:
            variable.set_value(variable.get_curr_domain().pop())
            new_assignments.update({variable: variable.get_value()})
    for constraint in csp.get_constraints():
        if constraint.get_name().startswith('NValuesConstraint_'):
            ship_parts_required = int(constraint.get_name()[-1])
            curr_num_ship_parts = sum(1 for variable in constraint.get_target_variables() if variable.get_value() in ship_parts)
            if ship_parts_required == curr_num_ship_parts:
                for variable in constraint.get_target_variables():
                    if not variable.is_assigned():
                        variable.set_value('.')
                        new_assignments.update({variable: '.'})
    for variable in new_assignments:
        assert reduce_domains(csp, variable, new_assignments[variable])
    return backtracking_search(csp)


def backtracking_search(csp: CSP) -> List[Dict[Tuple[int, int], any]]:
    """Return all solutions that can extend from the current assignment"""
    # Select a variable to assign or return the current assignment for base case
    min_domain_size = math.inf
    variable_to_assign = None
    curr_assignment = {}
    for variable in csp.get_variables():
        if variable.is_assigned():
            curr_assignment.update({variable.get_name(): variable.get_value()})
        elif variable.get_curr_domain_size() < min_domain_size:
            min_domain_size = variable.get_curr_domain_size()
            variable_to_assign = variable
    if variable_to_assign is None:
        return [curr_assignment]

    # Try each value in the domain and see if it leads to some solutions
    solutions = []
    for value in variable_to_assign.get_curr_domain():
        variable_to_assign.set_value(value)
        if reduce_domains(csp, variable_to_assign, value):
            solutions.extend(backtracking_search(csp))
        variable_to_assign.unassign()
        Variable.restore_values(variable_to_assign, value)

    return solutions


def reduce_domains(csp: CSP, reason_variable: Variable, reason_value: any) -> bool:
    # Forward checking
    constraints_involved = csp.get_constraints_of_variable(reason_variable)
    for constraint in constraints_involved:
        if constraint.get_name().startswith('NValuesConstraint_') and reason_value in ship_parts:
            ship_parts_required = int(constraint.get_name()[-1])
            curr_num_ship_parts = sum(
                1 for variable in constraint.get_target_variables() if variable.get_value() in ship_parts)
            if curr_num_ship_parts == ship_parts_required:
                for variable in constraint.get_target_variables():
                    if not variable.is_assigned():
                        if variable.value_in_curr_domain('.'):
                            values_to_remove = []
                            for value in variable.get_curr_domain():
                                if value != '.':
                                    values_to_remove.append(value)
                            for value in values_to_remove:
                                variable.remove_value_from_curr_domain(value, reason_variable, reason_value)
                        else:
                            return False
                continue
        for variable in constraint.get_target_variables():
            if not variable.is_assigned():
                values_to_remove = []
                for value in variable.get_curr_domain():
                    if not constraint.has_support(variable, value):
                        values_to_remove.append(value)
                        if len(values_to_remove) == variable.get_curr_domain_size():
                            return False
                for value in values_to_remove:
                    variable.remove_value_from_curr_domain(value, reason_variable, reason_value)

    # AC3
    ac3_constraints = set()
    for constraint in csp.get_constraints():
        if constraint.get_num_target_variables() == constraint.get_num_unassigned_variables() == 2:
            for variable in constraint.get_target_variables():
                ac3_constraints.add((variable, constraint))
    while len(ac3_constraints) > 0:
        variable, constraint = ac3_constraints.pop()
        values_to_remove = []
        for value in variable.get_curr_domain():
            if not constraint.has_support(variable, value):
                values_to_remove.append(value)
                if len(values_to_remove) == variable.get_curr_domain_size():
                    return False
        for value in values_to_remove:
            variable.remove_value_from_curr_domain(value, reason_variable, reason_value)
        if len(values_to_remove) > 0:
            for related_constraint in csp.get_constraints_of_variable(variable):
                if related_constraint.get_num_target_variables() == related_constraint.get_num_unassigned_variables() == 2:
                    for related_variable in related_constraint.get_target_variables():
                        if related_variable not in constraint.get_target_variables():
                            ac3_constraints.add((related_variable, related_constraint))

    return True


def find_solution_that_satisfies_ship_constraints(solutions: List[Dict[Tuple[int, int], any]], ship_constraints: Dict[str, int]) -> Dict[Tuple[int, int], any]:
    # check for mistaken M and change them to S or ship heads
    for solution in solutions:
        curr_ships = {'submarines': 0, 'destroyers': 0, 'cruisers': 0, 'battleships': 0}
        for i, j in solution:
            if solution[(i, j)] == 'S':
                curr_ships['submarines'] += 1
            elif solution[(i, j)] in {'^', '<'}:
                ship_type = identify_ship(solution, (i, j))
                if ship_type in curr_ships:
                    curr_ships[ship_type] += 1
                else:
                    break
        if curr_ships == ship_constraints:
            return solution


def identify_ship(solution: Dict[Tuple[int, int], any], ship_start: Tuple[int, int]) -> str:
    i, j = ship_start
    if solution[(i, j)] == '^':
        if (i + 1, j) in solution and solution[(i + 1, j)] == 'v':
            return 'destroyers'
        if (i + 1, j) in solution and solution[(i + 1, j)] == 'M' and (i + 2, j) in solution and solution[(i + 2, j)] == 'v':
            return 'cruisers'
        if (i + 1, j) in solution and solution[(i + 1, j)] == 'M' and (i + 2, j) in solution and solution[(i + 2, j)] == 'M' and (i + 3, j) in solution and solution[(i + 3, j)] == 'v':
            return 'battleships'
    if solution[(i, j)] == '<':
        if (i, j + 1) in solution and solution[(i, j + 1)] == '>':
            return 'destroyers'
        if (i, j + 1) in solution and solution[(i, j + 1)] == 'M' and (i, j + 2) in solution and solution[(i, j + 2)] == '>':
            return 'cruisers'
        if (i, j + 1) in solution and solution[(i, j + 1)] == 'M' and (i, j + 2) in solution and solution[(i, j + 2)] == 'M' and (i, j + 3) in solution and solution[(i, j + 3)] == '>':
            return 'battleships'
    return ''


#====================================================================================


def read_from_file(filename: str) -> Tuple[CSP, Dict[Variable, any], Dict[str, int], int]:
    f = open(filename)
    lines = f.readlines()
    N = len(lines[0]) - 1
    variables, row_list, col_list = create_variables(N)
    constraints, initial_assignments = create_constraints(lines[0].rstrip(), lines[1].rstrip(), row_list, col_list)
    initial_assignments.update(assign_initial_variables(row_list, lines))
    ship_constraints = {'submarines': int(lines[2][0]), 'destroyers': int(lines[2][1]), 'cruisers': int(lines[2][2]), 'battleships': int(lines[2][3])}
    return CSP('battle', variables, constraints), initial_assignments, ship_constraints, N


def create_variables(N: int) -> Tuple[Set[Variable], List[List[Variable]], List[List[Variable]]]:
    variables, row_list, col_list = set(), [], []
    for i in range(N):
        row_list.append([])
        for j in range(N):
            variable = Variable((i, j), {'.', 'S', '<', '>', '^', 'v', 'M'})
            variables.add(variable)
            row_list[-1].append(variable)
            if i == 0:
                col_list.append([variable])
            else:
                col_list[j].append(variable)
    return variables, row_list, col_list


def create_constraints(row_constraints: str, col_constraints: str, row_list: List[List[Variable]], col_list: List[List[Variable]]) -> Tuple[Set[Constraint], Dict[Variable, any]]:
    constraints = set()

    # Create row and col constraints and make 0 rows/columns all water
    initial_assignments = {}
    for i in range(len(row_list)):
        name = 'row_' + str(i) + '_' + row_constraints[i]
        bound = int(row_constraints[i])
        if bound == 0:
            for variable in row_list[i]:
                variable.set_value('.')
                initial_assignments.update({variable: '.'})
        else:
            constraints.add(NValuesConstraint(name, set(row_list[i]), ship_parts, bound, bound))
    for j in range(len(col_list)):
        name = 'col_' + str(j) + '_' + col_constraints[j]
        bound = int(col_constraints[j])
        if bound == 0:
            for variable in col_list[j]:
                variable.set_value('.')
                initial_assignments.update({variable: '.'})
        else:
            constraints.add(NValuesConstraint(name, set(col_list[j]), ship_parts, bound, bound))

    # Create horizontal and vertical neighbour constraints
    for i in range(len(row_list)):
        for j in range(len(col_list) - 1):
            variable_1, variable_2 = row_list[i][j], row_list[i][j + 1]
            name = 'horizontal_' + str(variable_1.get_name())
            target_variables = {variable_1, variable_2}
            satisfying_assignments = get_horizontal_neighbour_satisfying_assignments(variable_1, variable_2, len(col_list))
            constraints.add(TableConstraint(name, target_variables, satisfying_assignments))
    for j in range(len(col_list)):
        for i in range(len(row_list) - 1):
            variable_1, variable_2 = col_list[j][i], col_list[j][i + 1]
            name = 'vertical_' + str(variable_1.get_name())
            target_variables = {variable_1, variable_2}
            satisfying_assignments = get_vertical_neighbour_satisfying_assignments(variable_1, variable_2, len(row_list))
            constraints.add(TableConstraint(name, target_variables, satisfying_assignments))

    # Create diagonal neighbour constraints
    for i in range(len(row_list) - 1):
        for j in range(len(col_list)):
            variable_1 = row_list[i][j]
            if j > 0:
                variable_2 = row_list[i + 1][j - 1]
                name = 'diagonal_left_' + str(variable_1.get_name())
                target_variables = {variable_1, variable_2}
                constraints.add(AtLeastOneConstraint(name, target_variables, '.'))
            if j < len(col_list) - 1:
                variable_2 = row_list[i + 1][j + 1]
                name = 'diagonal_right_' + str(variable_1.get_name())
                target_variables = {variable_1, variable_2}
                constraints.add(AtLeastOneConstraint(name, target_variables, '.'))

    return constraints, initial_assignments


def get_horizontal_neighbour_satisfying_assignments(variable_1: Variable, variable_2: Variable, N: int) -> List[Dict[Variable, any]]:
    satisfying_assignments = [{variable_1: '.', variable_2: '.'}, {variable_1: '.', variable_2: 'S'}, {variable_1: 'S', variable_2: '.'}, {variable_1: '<', variable_2: '>'}]
    i, j = variable_1.get_name()
    if i > 0:
        satisfying_assignments.extend([{variable_1: 'v', variable_2: '.'}, {variable_1: '.', variable_2: 'v'}])
    if i < N - 1:
        satisfying_assignments.extend([{variable_1: '^', variable_2: '.'}, {variable_1: '.', variable_2: '^'}])
    if 0 < i < N - 1:
        satisfying_assignments.extend([{variable_1: '.', variable_2: 'M'},  {variable_1: 'M', variable_2: '.'}])
    if j > 0:
        satisfying_assignments.extend([{variable_1: 'M', variable_2: '>'}, {variable_1: '>', variable_2: '.'}])
    if j < N - 2:
        satisfying_assignments.extend([{variable_1: '<', variable_2: 'M'}, {variable_1: '.', variable_2: '<'}])
    if 0 < j < N - 2:
        satisfying_assignments.extend([{variable_1: 'M', variable_2: 'M'}])
    return satisfying_assignments


def get_vertical_neighbour_satisfying_assignments(variable_1: Variable, variable_2: Variable, N: int) -> List[Dict[Variable, any]]:
    satisfying_assignments = [{variable_1: '.', variable_2: '.'}, {variable_1: '.', variable_2: 'S'}, {variable_1: 'S', variable_2: '.'}, {variable_1: '^', variable_2: 'v'}]
    i, j = variable_1.get_name()
    if i > 0:
        satisfying_assignments.extend([{variable_1: 'M', variable_2: 'v'}, {variable_1: 'v', variable_2: '.'}])
    if i < N - 2:
        satisfying_assignments.extend([{variable_1: '^', variable_2: 'M'}, {variable_1: '.', variable_2: '^'}])
    if 0 < i < N - 2:
        satisfying_assignments.extend([{variable_1: 'M', variable_2: 'M'}])
    if j > 0:
        satisfying_assignments.extend([{variable_1: '>', variable_2: '.'}, {variable_1: '.', variable_2: '>'}])
    if j < N - 1:
        satisfying_assignments.extend([{variable_1: '<', variable_2: '.'}, {variable_1: '.', variable_2: '<'}])
    if 0 < j < N - 1:
        satisfying_assignments.extend([{variable_1: '.', variable_2: 'M'},  {variable_1: 'M', variable_2: '.'}])
    return satisfying_assignments


def assign_initial_variables(row_list: List[List[Variable]], lines: List[str]) -> Dict[Variable, any]:
    initial_assignments = {}
    for i in range(len(row_list)):
        for j in range(len(row_list[i])):
            variable = row_list[i][j]
            input_value = lines[3 + i][j]
            if input_value != '0':
                variable.set_value(input_value)
                initial_assignments.update({variable: input_value})
    return initial_assignments


def write_to_file(filename: str, solution: Dict[Tuple[int, int], any], N: int):
    output_file = open(filename, "w")
    grid = [['0' for _ in range(N)] for _ in range(N)]
    for i, j in solution:
        grid[i][j] = solution[(i, j)]
    for line in grid:
        output_file.write(''.join(line) + '\n')
    output_file.close()


#====================================================================================


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()
    csp, initial_assignments, ship_constraints, N = read_from_file(args.inputfile)
    solutions = find_solutions(csp, initial_assignments)
    solution = find_solution_that_satisfies_ship_constraints(solutions, ship_constraints)
    write_to_file(args.outputfile, solution, N)
