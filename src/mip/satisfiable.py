try:
    from docplex.mp.model import Model
    from docplex.cp.model import CpoModel
    from docplex.cp.expression import integer_var_list
    has_cplex = True
except:
    from pyscipopt import Model
    has_cplex = False


def compute_color_to_indices(coloring):
    colors = set(coloring)
    return {c: [p for p, cp in enumerate(coloring) if cp == c] for c in colors}

def build_model(edges, coloring, technique="LP"):
    if technique == "CP":
        # CP model cannot be iteratively updated and will be recreated for each solve.
        return None
    elif technique == "LP":
        if has_cplex:
            return build_model_cplex(edges, coloring)
        else:
            # I did not manage to make it work with reusing the model for
            # different states, so the model is being rebuilt every time.
            return None
    else:
        print(f"Unknown modelling technique '{technique}'")

def is_state_valid(m, edges, coloring, abstract_state, technique="LP"):
    if technique == "CP":
        return is_state_valid_cp(m, edges, coloring, abstract_state)
    elif technique == "LP":
        if has_cplex:
            return is_state_valid_cplex(m, edges, coloring, abstract_state)
        else:
            return is_state_valid_scip(m, edges, coloring, abstract_state)
    else:
        print(f"Unknown modelling technique '{technique}'")

# CP ---------------------------------------------------------------------------

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

# CPLEX ------------------------------------------------------------------------

def build_model_cplex(edges, coloring):
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


def is_state_valid_cplex(m, edges, coloring, abstract_state):
    for color in set(coloring):
        m.get_constraint_by_index(color).rhs = abstract_state[color]
    m.solve(log_output=False)
    return m.solve_details.status != "integer infeasible"

# SCIP -------------------------------------------------------------------------

def build_model_scip(edges, coloring):
    num_nodes = len(coloring)
    m = Model()
    m.setObjective(0, "minimize")
    con_vars = []
    for i in range(num_nodes):
        con_vars.append(m.addVar(vtype="B"))

    color_dict = compute_color_to_indices(coloring)
    for color, indices in color_dict.items():
        m.addCons(sum(con_vars[i] for i in indices) == 0)

    for i, j in edges:
        m.addCons(con_vars[i] + con_vars[j] <= 1)

    return m


def is_state_valid_scip(m, edges, coloring, abstract_state):
    m = build_model_scip(edges, coloring)
    constraints = m.getConss()
    for color in set(coloring):
        m.chgRhs(constraints[color], abstract_state[color])
        m.chgLhs(constraints[color], abstract_state[color])
    m.hideOutput()
    m.optimize()
    return m.getStatus() != "infeasible"
