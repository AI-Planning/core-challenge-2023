
try:
    from docplex.mp.model import Model
    from docplex.cp.model import CpoModel
    from docplex.cp.expression import integer_var_list
except:
    import sys
    sys.exit(1)


def compute_color_to_indices(coloring):
    colors = set(coloring)
    return {c: [p for p, cp in enumerate(coloring) if cp == c] for c in colors}

def build_model(edges, coloring, technique="LP"):
    if technique == "CP":
        # CP model cannot be iteratively updated and will be recreated for each solve.
        return None
    elif technique == "LP":
        return build_model_lp(edges, coloring)
    else:
        print(f"Unknown modelling technique '{technique}'")

def is_state_valid(m, edges, coloring, abstract_state, technique="LP"):
    if technique == "CP":
        return is_state_valid_cp(m, edges, coloring, abstract_state)
    elif technique == "LP":
        return is_state_valid_lp(m, edges, coloring, abstract_state)
    else:
        print(f"Unknown modelling technique '{technique}'")

# CP---------------------

def build_model_cp(edges, coloring, abstract_state):
    num_nodes = len(coloring)
    m = CpoModel()
    x = m.integer_var_list(num_nodes, 0, 1)

    color_dict = compute_color_to_indices(coloring)
    for color, indices in color_dict.items():
        m.add_constraint(sum(x[i] for i in indices) == abstract_state[color])

    for i, j in edges:
        m.add_constraint(x[i] + x[j] <= 1)

    return m


def is_state_valid_cp(m, edges, coloring, abstract_state):
    m = build_model_cp(edges, coloring, abstract_state)
    result = m.solve(log_output=None).get_solve_status()
    return result != "Infeasible"

# LP---------------------

def build_model_lp(edges, coloring):
    num_nodes = len(coloring)
    m = Model()
    m.set_objective("min", 0)
    x = m.binary_var_list(num_nodes)

    color_dict = compute_color_to_indices(coloring)
    for color, indices in color_dict.items():
        m.add_constraint(sum(x[i] for i in indices) == 0)

    for i, j in edges:
        m.add_constraint(x[i] + x[j] <= 1)

    return m


def is_state_valid_lp(m, edges, coloring, abstract_state):
    for color in set(coloring):
        m.get_constraint_by_index(color).rhs = abstract_state[color]
    m.solve(log_output=False)
    return m.solve_details.status != "integer infeasible"
