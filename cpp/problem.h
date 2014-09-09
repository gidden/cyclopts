#ifndef CYCLOPTS_PROBLEM_H_
#define CYCLOPTS_PROBLEM_H_

#include <string>

namespace cyclopts {

/// A generic container for problem instance solutions
class ProbSolution {
 public:
  /// @param time the solution time
  /// @param objective the solution objective
  /// @param type the problem type
  ProbSolution(double time = 0, double objective = 0, std::string type = "");
  
  double time;
  double objective;
  std::string type;
};

/// A container class for solver indentifying parameters.
class Solver {
 public:
  /// @param type the type of solver
  explicit Solver(std::string type = "cbc");

  std::string type;
};

} // namespace cyclopts

#endif // CYCLOPTS_PROBLEM_H_
