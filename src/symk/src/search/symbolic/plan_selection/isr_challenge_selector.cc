#include "isr_challenge_selector.h"

#include "../../utils/logging.h"

using namespace std;

namespace symbolic {
IsrChallengeSelector::IsrChallengeSelector(const options::Options &opts)
    : IterativeCostSelector(opts) {
}

void IsrChallengeSelector::init(shared_ptr<SymVariables> sym_vars,
                                const shared_ptr<AbstractTask> &task,
                                PlanManager &plan_manager) {
    IterativeCostSelector::init(sym_vars, task, plan_manager);

    FactPair hand_full = get_hand_full_fact(task);
    artifical_states = sym_vars->preBDD(hand_full.var, hand_full.value);
    // sym_vars->to_dot(artifical_states, "hand_full.dot");
}

BDD IsrChallengeSelector::ignore_in_simple_reconstruction() const {
    return artifical_states;
}

FactPair IsrChallengeSelector::get_hand_full_fact(
    const shared_ptr<AbstractTask> &task) const {
    for (int var = 0; var < task->get_num_variables(); ++var) {
        if (task->get_variable_name(var) == "hand") {
            for (int val = 0; val < task->get_variable_domain_size(var); ++val) {
                FactPair hand_full(var, val);
                if (task->get_fact_name(hand_full) == "Atom full()") {
                    return hand_full;
                }
            }
        }
    }
    cerr << "No fact with name \"Atom full()\" found!" << endl;
    utils::exit_with(utils::ExitCode::SEARCH_INPUT_ERROR);
    return FactPair(-1, -1);
}

static shared_ptr<PlanDataBase> _parse(OptionParser &parser) {
    IterativeCostSelector::add_options_to_parser(parser);

    Options opts = parser.parse();
    if (parser.dry_run())
        return nullptr;
    return make_shared<IsrChallengeSelector>(opts);
}

static Plugin<PlanDataBase> _plugin("isr_challenge", _parse);
}
