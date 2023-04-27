#!/usr/bin/env python3

from parse import parse_col_file, parse_dat_file
from search import DepthFirstSearch

from collections import Counter
import sys



def color_of(p, start_state, goal_state):
    return (1 if p in start_state else 0) + (2 if p in goal_state else 0)


def get_abstract_state(concrete_state, coloring):
    count = Counter([coloring[p] for p in range(len(coloring)) if p in concrete_state])
    num_colors = max(coloring) + 1
    return tuple(count[color] for color in range(num_colors))


def main():
    num_nodes, edges = parse_col_file(sys.argv[1])
    start_state, goal_state = parse_dat_file(sys.argv[2])
    coloring = [color_of(p, start_state, goal_state) for p in range(num_nodes)]

    abs_initial_state = get_abstract_state(start_state, coloring)
    abs_goal_state = get_abstract_state(goal_state, coloring)

    search = DepthFirstSearch(edges, coloring)
    result = search.run(abs_initial_state, abs_goal_state)
    if result:
        print("Unknown")
        sys.exit(1)
    else:
        print("Unsolvable")
        sys.exit(10)

if __name__ == "__main__":
    main()
