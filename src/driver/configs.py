from pathlib import Path
import psutil
import subprocess

SCRIPT_DIR = Path(__file__).parent
SOLVER_DIR = SCRIPT_DIR.parent
SCORPION = str(SOLVER_DIR / "scorpion/fast-downward.py")
SYMK = str(SOLVER_DIR / "symk/fast-downward.py")
MIP_SOLVER = str(SOLVER_DIR / "mip/check-unsolvability.py")


class Reponse(object):
    def __init__(self, plan, cost, is_shortest, is_longest):
        "Use plan=None, cost=float('inf'), is_shortest=True for proven unsolvability."
        self.plan = plan
        self.cost = cost
        self.is_shortest = is_shortest
        self.is_longest = is_longest

class Config(object):
    def __init__(self):
        self.response = None

    def run(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        raise NotImplementedError


class PortfolioConfig(Config):
    TIME_BUFFER_FOR_RESPONSE = 55
    TIME_BUFFER_FOR_SOLVERS = 5
    MEMORY_BUFFER_FOR_DRIVER = 200 * 1024 * 1024

    def __init__(self, components):
        Config.__init__(self)
        self.components = components

    def run(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        # TODO: run components in parallel, react to one of them finishing, decide wether to keep the others running
        component_memory_limit = (memory_limit - PortfolioConfig.MEMORY_BUFFER_FOR_DRIVER) // len(self.components)

        component_time_limit = time_limit - PortfolioConfig.TIME_BUFFER_FOR_RESPONSE - PortfolioConfig.TIME_BUFFER_FOR_SOLVERS

        processes_ids = []
        for c in self.components:
            process = subprocess.Popen(c.cmd)
            processes_ids.append(psutil.Process(process.pid)]

        def on_terminate(process):
            pass

        gone, alive = psutil.wait_procs(processes_ids, timeout=time_limit - PortfolioConfig.TIME_BUFFER_FOR_RESPONSE, callback=on_terminate)


class SingleConfig(Config):
    def __init__(self, cmd):
        Config.__init__(self)
        self.cmd = cmd

    def run(self, run_dir, memory_limit, time_limit, col_filename, dat_filename, sas_filename):
        # TODO replace placeholders in cmd
        # TODO run cmd with limits
        # TODO call on_terminate with run_dir and exit code
        pass

    def on_terminate(self):
        # TODO: parse any plans
        # self.response = ...
        pass


class ScorpionAnytimeConfig(SingleConfig):
    def __init__(self):
        cmd = [SCORPION, "{sas_filename}",
                "--landmarks", "lmg=lm_hm(use_orders=false, m=1)",
                "--evaluator", "hlm=lmcount(lmg, admissible=True, pref=false)",
                "--search", """iterated([
                    eager(single(hlm)),
                    lazy_greedy([hlm]),
                    lazy_wastar([hlm],w=5),
                    lazy_wastar([hlm],w=3),
                    lazy_wastar([hlm],w=2),
                    lazy_wastar([hlm],w=1)
                    ],repeat_last=true,continue_on_fail=false)"""]
        super().__init__(cmd)


class ScorpionFirstSolutionConfig(SingleConfig):
    def __init__(self):
        cmd = [SCORPION, "{sas_filename}",
                "--landmarks", "lmg=lm_hm(use_orders=false, m=1)",
                "--evaluator", "hlm=lmcount(lmg, admissible=True, pref=false)",
                "--search", "eager(single(hlm))"]
        super().__init__(cmd)

class SymKShortSolutionConfig(SingleConfig):
    def __init__(self):
        cmd = [SYMK, "{sas_filename}", "--search", "sym-fw()"]
        super().__init__(cmd)

class SymKLongSolutionConfig(SingleConfig):
    def __init__(self):
        cmd = [SYMK, "{sas_filename}", "--search",
               "symk-fw(plan_selection=isr_challenge(num_plans=infinity),silent=true,simple=true)"]
        super().__init__(cmd)

class MIPConfig(SingleConfig):
    def __init__(self):
        cmd = [MIP_SOLVER, "{col_filename}", "{dat_filename}"]
        super().__init__(cmd)


CONFIGS = {
    "shortest-single": ScorpionAnytimeConfig(),
    "shortest-portfolio": PortfolioConfig([
        ScorpionAnytimeConfig(),
        SymKShortSolutionConfig(),
        MIPConfig(),
    ]),
    "existent-single": ScorpionFirstSolutionConfig(),
    "existent-portfolio": PortfolioConfig([
        ScorpionFirstSolutionConfig(),
        SymKShortSolutionConfig(),
        MIPConfig(),
    ]),
    "longest-single": SymKLongSolutionConfig(),
    "longest-portfolio": PortfolioConfig([
        SymKLongSolutionConfig(),
        ScorpionFirstSolutionConfig(),
    ]),
}