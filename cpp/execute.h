#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

#include <cstddef>
#include <string>

/// place holder until a distribution class is added
class Distribution {
};

/// a simple template class to encapsulate an execution run control parameter
/// @warning if a distribution is provided to the Param, it will take charge of
/// its deletion
template <class T>
class Param {
 public:
  /// @param val the (possibly average) value of the parameter
  /// @param dist an optional distribution
  /// @warning if dist is provided, the Param takes ownership of it (i.e., will
  /// delete it)
  Param(T val, Distribution* dist = NULL) : val_(val), dist_(dist) { }

  ~Param() { if(dist_ != NULL) delete dist_; }
  
  inline T val() const { return val_; }

  /// sample a value; subclasses can override to provide custom sampling
  virtual T sample() const { if(dist_ == NULL) return val_; }

 private:
  T val_;
  Distribution* dist_;
};

/// number of assemblies
class AssemblyParam: public Param<int> {
 public:
  AssemblyParam(int val = 1, Distribution* dist = NULL) : Param<int>(val, dist) {};
};

/// defines the run control parameters for a reactor-request-based exchange
///
/// @param n_supply the number of supplier node groups
/// @param n_consume the number of consumer node groups
/// @param con_node_avg the average number of consumer nodes in a group
/// @param n_commods the number of commodities
/// @param con_commod_avg the average number of commodities in a consumer node
/// group
/// @param avg_commod_sup the average number of commodities that a supplier
/// can supply (i.e., supply node groups per supplier)
/// @param excl_prob the probability that a consumer node will be exclusive
/// @param connect_prob the probability that a connection is made between a
/// request and supply of the same commodity
/// @param avg_sup_caps average number of supply capacities per group
/// @param avg_sup_caps average number of demand capacities per group
class RequestRC {
 public:
  int i();
  
 private:
  int i_;
};

class SupplyRC {
 public:
  int i();
  
 private:
  int i_;
};

/// constructs and runs a reactor-request resource exchange
///
void run_rxtr_req(RequestRC rc);

void test();

#endif // CYCLOPTS_EXECUTE_H_
