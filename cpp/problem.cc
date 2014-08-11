#include "problem.h"

namespace cyclopts {

ProbSolution::ProbSolution(double time, double objective, std::string type)
    : time(time),
      objective(objective), 
      type(type) { };

} // namespace cyclopts
