from natsort import natsorted
from pathlib import Path
import psutil
import re
import resource

from compile import decode_plan

SCRIPT_DIR = Path(__file__).parent
SOLVER_DIR = SCRIPT_DIR.parent
SCORPION = str(SOLVER_DIR / "scorpion/fast-downward.py")
SYMK = str(SOLVER_DIR / "symk/fast-downward.py")
MIP_SOLVER = str(SOLVER_DIR / "mip/check-unsolvability.py")

SHORTEST_TRACK = "shortest"
LONGEST_TRACK = "longest"
EXISTENT_TRACK = "existent"

EXIT_SUCCESS = 0
EXIT_SEARCH_UNSOLVED_INCOMPLETE = 12


class Response(object):
    def __init__(self, plan, cost, is_shortest, is_longest):
        """
        Use plan containing "a NO" together with cost=float('inf') and is_shortest=True for proven unsolvability.
        """
        self.plan = plan
        self.cost = cost
        self.is_shortest = is_shortest
        self.is_longest = is_longest

    def __str__(self):
        return self.plan

def generate_unsolvable_response(dat_filename: Path):
    plan_lines = dat_filename.read_text() + "\na NO"
    return Response(plan_lines, float("inf"), is_shortest=True, is_longest=True)


def better_response(r1, r2, track):
    for response, other in [(r1, r2), (r2, r1)]:
        if response is None:
            # Any solution is better than nothing.
            return other
        if response.cost == float("inf") and response.is_shortest:
            # Instance is guaranteed to be unsolvable.
            return response

    # If we end up here, both solutions have values.
    if track == SHORTEST_TRACK:
        if r1.cost <= r2.cost:
            return r1
        else:
            return r2
    elif track == LONGEST_TRACK:
        if r1.cost >= r2.cost and r1.cost < float("inf"):
            return r1
        else:
            return r2
    elif track == EXISTENT_TRACK:
        if r1.cost < float("inf"):
            return r1
        else:
            return r2


def is_best_response(response, track):
    if response is None:
        return False
    elif response.cost == float("inf") and response.is_shortest:
        return True
    elif track == SHORTEST_TRACK:
        return response.is_shortest
    elif track == LONGEST_TRACK:
        return response.is_longest
    elif track == EXISTENT_TRACK:
        return response.cost < float("inf")


TIME_BUFFER_FOR_RESPONSE = 55
TIME_BUFFER_FOR_SOLVERS = 4
TIME_BUFFER_FOR_TERMINATE = 1
MEMORY_BUFFER_FOR_DRIVER = 200 * 1024 * 1024


class PortfolioConfig(object):

    def __init__(self, track, components):
        self.track = track
        self.components = components

    def run(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        """
        Run components in parallel, react to one of them finishing, decide wether to keep the others running.
        """
        component_memory_limit = (memory_limit - MEMORY_BUFFER_FOR_DRIVER) // len(self.components)
        component_time_limit = time_limit - TIME_BUFFER_FOR_RESPONSE - TIME_BUFFER_FOR_SOLVERS - TIME_BUFFER_FOR_TERMINATE

        best_response = None
        processes = []
        for i, c in enumerate(self.components):
            component_run_dir_path = Path(run_dir) / f"component_{i}"
            component_run_dir_path.mkdir()
            process = c.start(
                str(component_run_dir_path), component_memory_limit, component_time_limit,
                col_filename, dat_filename, sas_filename)
            processes.append(process)

        def on_process_terminate(process):
            try:
                new_response = process.command.parse_reponse(process, self.track)
            except:
                # Silently ignore errors in the parsers so they don't kill the other components.
                # We also do not want to print anything because we should only print the solution.
                new_response = None
            nonlocal best_response
            best_response = better_response(best_response, new_response, self.track)
            if is_best_response(best_response, self.track):
                terminate_all(processes)

        psutil.wait_procs(processes, timeout=time_limit - TIME_BUFFER_FOR_RESPONSE, callback=on_process_terminate)
        return best_response


def terminate_all(processes):
    for p in processes:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(processes, timeout=TIME_BUFFER_FOR_TERMINATE)
    for p in processes:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass


class SingleConfig(object):
    def __init__(self, track, component):
        self.track = track
        self.component = component

    def run(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        component_memory_limit = memory_limit - MEMORY_BUFFER_FOR_DRIVER
        component_time_limit = time_limit - TIME_BUFFER_FOR_RESPONSE - TIME_BUFFER_FOR_SOLVERS
        process = self.component.start(run_dir, component_memory_limit, component_time_limit, col_filename, dat_filename, sas_filename)
        process.wait()
        return self.component.parse_reponse(process, self.track)


class PlannerCommand(object):
    def __init__(self, cmd):
        self.cmd = cmd

    def start(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        def prepare_call():
            resource.setrlimit(resource.RLIMIT_CPU, (time_limit-1, time_limit))
            _, hard_mem_limit = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, hard_mem_limit))

        # Replace placeholders (limits, inputs) in cmd.
        cmd = [part.format(
            run_dir=run_dir,
            memory_limit=memory_limit,
            time_limit=time_limit,
            col_filename=col_filename,
            dat_filename=dat_filename,
            sas_filename=sas_filename
        ) for part in self.cmd]
        # Start the planner.
        out_file = open(f"{run_dir}/run.log", "w")
        err_file = open(f"{run_dir}/run.err", "w")
        process = psutil.Popen(cmd, cwd=run_dir, stdout=out_file, stderr=err_file, preexec_fn=prepare_call)
        # Store information potentially needed by the parser.
        process.command = self
        process.run_dir = run_dir
        process.memory_limit = memory_limit
        process.time_limit = time_limit
        process.col_filename = col_filename
        process.dat_filename = dat_filename
        process.sas_filename = sas_filename
        return process

    def parse_reponse(self, process, track):
        # implement in derived classes: parse any plans, select the best one and return a response
        return None


def generate_unsolvable_response(dat_filename: Path):
    plan_lines = dat_filename.read_text() + "\na NO"
    return Response(plan_lines, float("inf"), is_shortest=True, is_longest=True)

def parse_valid_plan_with_highest_id(run_dir: Path, dat_filename: Path):
    instance = dat_filename.read_text()
    instance_lines = instance.splitlines()
    assert "s " == instance_lines[0][0:2]
    assert "t " == instance_lines[1][0:2]
    init = set(instance_lines[0][2:].split())
    goal = set(instance_lines[1][2:].split())

    for plan_file in natsorted(run_dir.glob("sas_plan*"), reverse=True):
        lines = plan_file.read_text().splitlines()
        if not lines:
            continue
        *actions, cost_line = lines
        match = re.match(r"; cost = (\d+) \(unit cost\)", cost_line)
        if not match:
            continue
        plan, cost = decode_plan(actions, init, goal)
        if plan is not None:
            return instance + plan, cost
    return None, None


def parse_scorpion_response(process, track):
    if process.returncode == EXIT_SEARCH_UNSOLVED_INCOMPLETE:
        return generate_unsolvable_response(Path(process.dat_filename))

    best_plan, cost = parse_valid_plan_with_highest_id(Path(process.run_dir), Path(process.dat_filename))
    if best_plan is None:
        return None

    with open(f"{process.run_dir}/run.log") as f:
        exhausted_state_space = any("Completely explored state space -- no solution!" in line for line in f)
    return Response(best_plan, cost, is_shortest=exhausted_state_space, is_longest=False)


def parse_symk_response(process, track):
    cost = None
    best_plan = None
    shortest_plan = False

    if process.returncode == EXIT_SEARCH_UNSOLVED_INCOMPLETE:
        return generate_unsolvable_response(Path(process.dat_filename))
    elif track == SHORTEST_TRACK or track == EXISTENT_TRACK:
        best_plan, cost = parse_valid_plan_with_highest_id(Path(process.run_dir), Path(process.dat_filename))
        if best_plan is not None:
            shortest_plan = True
    else:
        best_plan, cost = parse_valid_plan_with_highest_id(Path(process.run_dir), Path(process.dat_filename))
        if best_plan is not None:
            shortest_plan = False

    assert not EXIT_SUCCESS or best_plan is not None

    if best_plan is not None:
        return Response(best_plan, cost, is_shortest=shortest_plan, is_longest=False)
    assert cost == None
    return None


class ScorpionAnytime(PlannerCommand):
    def __init__(self):
        cmd = [SCORPION, "{sas_filename}",
               "--evaluator", "h=goalcount()",
               "--search", """iterated([
                    eager(single(h)),
                    eager_wastar([h],w=5),
                    eager_wastar([h],w=3),
                    eager_wastar([h],w=2),
                    astar(h)
                    ],repeat_last=false,continue_on_fail=false)"""]
        super().__init__(cmd)

    def parse_reponse(self, process, track):
        return parse_scorpion_response(process, track)


class ScorpionFirstSolution(PlannerCommand):
    def __init__(self):
        cmd = [SCORPION, "{sas_filename}",
               "--evaluator", "h=goalcount()",
               "--search", "eager(single(h))"]
        super().__init__(cmd)

    def parse_reponse(self, process, track):
        return parse_scorpion_response(process, track)


class SymKShortSolution(PlannerCommand):
    def __init__(self):
        cmd = [SYMK, "{sas_filename}", "--search", "sym-fw()"]
        super().__init__(cmd)

    def parse_reponse(self, process, track):
        return parse_symk_response(process, track)


class SymKLongSolution(PlannerCommand):
    def __init__(self):
        cmd = [SYMK, "{sas_filename}", "--search",
               "symk-fw(plan_selection=isr_challenge(num_plans=infinity),silent=true,simple=true)"]
        super().__init__(cmd)

    def parse_reponse(self, process, track):
        return parse_symk_response(process, track)


class MIPPlanner(PlannerCommand):
    def __init__(self):
        cmd = [MIP_SOLVER, "{col_filename}", "{dat_filename}"]
        super().__init__(cmd)

    def parse_reponse(self, process, track):
        if process.returncode == 10:
            return generate_unsolvable_response(Path(process.dat_filename))
        else:
            return None


CONFIGS = {
    "shortest-single": SingleConfig(SHORTEST_TRACK,
        ScorpionAnytime()
    ),
    "shortest-portfolio": PortfolioConfig(SHORTEST_TRACK, [
        ScorpionAnytime(),
        SymKShortSolution(),
    ]),
    "existent-single": SingleConfig(EXISTENT_TRACK,
        ScorpionFirstSolution()
    ),
    "existent-portfolio": PortfolioConfig(EXISTENT_TRACK, [
        ScorpionFirstSolution(),
        SymKShortSolution(),
        MIPPlanner(),
    ]),
    "longest-single": SingleConfig(LONGEST_TRACK,
        SymKLongSolution()
    ),
    "longest-portfolio": PortfolioConfig(LONGEST_TRACK, [
        SymKLongSolution(),
        ScorpionFirstSolution(),
    ]),
}
