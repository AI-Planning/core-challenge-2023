#ifndef SYMBOLIC_ISR_CHALLENGE_SELECTOR_H
#define SYMBOLIC_ISR_CHALLENGE_SELECTOR_H

#include "iterative_cost_selector.h"
#include "../../option_parser.h"
#include "../../task_utils/task_properties.h"

using namespace std;

namespace symbolic {
class IsrChallengeSelector : public IterativeCostSelector {
public:
    IsrChallengeSelector(const options::Options &opts);
    ~IsrChallengeSelector() {}

    virtual void init(std::shared_ptr<SymVariables> sym_vars,
                      const std::shared_ptr<AbstractTask> &task,
                      PlanManager &plan_manager);

    virtual BDD ignore_in_simple_reconstruction() const;

    std::string tag() const override {return "Isr challenge selector";}

    static void add_options_to_parser(options::OptionParser &parser);

protected:
    BDD artifical_states;

    FactPair get_hand_full_fact(const shared_ptr<AbstractTask> &task) const;
};
}

#endif
