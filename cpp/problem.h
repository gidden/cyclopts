#ifndef CYCLOPTS_PROBLEM_SOLUTION_H_
#define CYCLOPTS_PROBLEM_SOLUTION_H_

#include <string>

namespace cyclopts {

/// a generic container for problem instance solutions
class ProbSolution {
 public:
  ProbSolution(double time = 0, double objective = 0, std::string type = "");
  
  double time;
  double objective;
  std::string type;
};

/// A container class for solver indentifying parameters.
class Solver {
 public:
  explicit Solver(std::string type = "cbc") : type(type) { };
  std::string type;
};

} // namespace cyclopts

#endif // CYCLOPTS_PROBLEM_SOLUTION_H_
