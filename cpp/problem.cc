#include "problem.h"

namespace cyclopts {

ProbSolution::ProbSolution(double time, double objective, std::string type)
    : time(time),
      objective(objective), 
      type(type) { };

Solver::Solver(std::string type) : type(type) { };

} // namespace cyclopts
