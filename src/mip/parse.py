def to_var_id(node):
    return int(node) - 1


def parse_col_file(filename):
    with open(filename) as f:
        edges = []
        num_nodes, num_edges = None, None
        num_parsed_edges = 0
        for line in f:
            args = line.split()
            assert args[0] == "c" or len(args) == 3
            if args[0] == "p":
                num_nodes, num_edges = int(args[1]), int(args[2])
            elif args[0] == "e":
                num_parsed_edges += 1
                v0, v1 = to_var_id(args[1]), to_var_id(args[2])
                assert 0 <= v0 <  num_nodes
                assert 0 <= v1 <  num_nodes
                edges.append((v0, v1))
    assert num_edges == num_parsed_edges
    return num_nodes, edges


def parse_dat_file(filename):
    start, target = None, None
    with open(filename) as f:
        for line in f:
            args = line.split()
            if args[0] == "s":
                start = set([to_var_id(x) for x in args[1:]])
            if args[0] == "t":
                target = set([to_var_id(x) for x in args[1:]])
    return start, target
