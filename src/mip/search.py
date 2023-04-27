from satisfiable import build_model, is_state_valid
import time

class DepthFirstSearch(object):
    def __init__(self, edges, coloring):
        self.edges = edges
        self.coloring = coloring
        self.model = build_model(edges, coloring)

    def _reset(self):
        self.queue = []
        self.closed = set()
        self.report_granularity = 1
        self.report_next = 1
        self.num_expanded = 0
        self.num_evaluated = 0
        self.started = time.time()

    def _push(self, s):
        self.queue.append(s)
        self.closed.add(s)

    def _pop(self):
        return self.queue.pop()

    def _get_successors(self, s):
        variables = range(len(s))
        for source in variables:
            for target in variables:
                if source != target and s[source] > 0:
                    succ = list(s)
                    succ[source] -= 1
                    succ[target] += 1
                    yield tuple(succ)


    def _is_state_valid(self, s):
        self.num_evaluated += 1
        return is_state_valid(self.model, self.edges, self.coloring, s)

    def _report(self):
        self.num_expanded += 1
        if self.num_expanded == self.report_next:
            show = True
            self.report_next += self.report_granularity
            if self.report_next % (self.report_granularity*10) == 0:
                self.report_granularity *= 10
            elapsed = time.time() - self.started
            states_per_second = self.num_evaluated / elapsed
            print(f"[{elapsed:0.2f}] "
                  f"Expanded {self.num_expanded} states; "
                  f"Evaluated {self.num_evaluated} states "
                  f"({states_per_second:0.2f} per second)")

    def _print_statistics(self):
        print(f"Total time: {time.time() - self.started:0.2f}")
        print(f"Expanded: {self.num_expanded}")


    def run(self, initial_state, goal_state):
        self._reset()
        self._push(initial_state)
        while self.queue:
            s = self._pop()
            self._report()
            for succ in self._get_successors(s):
                if succ not in self.closed and self._is_state_valid(succ):
                    if succ == goal_state:
                        self._print_statistics()
                        return True
                    self._push(succ)
        self._print_statistics()
        return False
