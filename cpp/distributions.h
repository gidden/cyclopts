#ifndef CYCLOPTS_GENERATOR_H_
#define CYCLOPTS_GENERATOR_H_

#include <string>

void run_exchange(int nsup, int ncon, double fraction, bool flag) {}

class Generator {
 public:
  Generator();

  std::string type() const { return type_; }

 private:
  std::string type_;
};

#endif // CYCLOPTS_GENERATOR_H_