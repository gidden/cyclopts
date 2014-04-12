#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

#include <string>
#include <map>
#include <vector>

/// A simple container class for an arc's id and its associated resource flow.
class ArcFlow {
public:
  ArcFlow() : id(-1), flow(0) { };
  ArcFlow(int id, double flow) : id(id), flow(flow) { };
  ArcFlow(const ArcFlow& other) : id(other.id), flow(other.flow) { };
  
  inline ArcFlow& operator=(const ArcFlow& other) {
    id = other.id;
    flow = other.flow;
    return *this;
  }
  inline bool operator==(const ArcFlow& other) {
    return id == other.id && flow == other.flow;
  }
  inline bool operator!=(const ArcFlow& other) {
    return !(this->operator==(other));
  }
  
  int id;
  double flow;
};

/// A simple container class for exchange solutions.
class Solution {
 public:
  std::vector<ArcFlow> flows;
  double time;
};

/// A container class for all parameters required to construct an instance of a
/// Cyclus ExchangeSolver.
class SolverParams {
 public:
  std::string type;
};

/// A container class for all parameters required to construct an instance of a
/// Cyclus ExchangeGraph.
class GraphParams {
 public:
  /// convenience function to populate entries for request groups
  void AddRequestGroup(int g);
  
  /// convenience function to populate entries for request nodes
  void AddRequestNode(int n, int g);

  /// convenience function to populate entries for supply groups
  void AddSupplyGroup(int g);
  
  /// convenience function to populate entries for supply nodes
  void AddSupplyNode(int n, int g);
  
  /// requester : their request nodes
  /// gets filled by AddRequestNode
  std::map<int, std::vector<int> > u_nodes_per_req;

  /// supplier : their supply nodes
  /// gets filled by AddSupplyNode
  std::map<int, std::vector<int> > v_nodes_per_sup;

  /// requester : request qty
  std::map<int, double> req_qty;

  /// requester or supplier : constraint rhs values 
  /// @warning all groups must have an entry
  std::map<int, std::vector<double> > constr_vals;

  /// request node : the default mass constraint coefficient
  /// note this is how multicommodity requests are taken into account
  /// @warning all request nodes must have an entry
  std::map<int, double> def_constr_coeff;

  /// node id to node quantity
  /// @warning all nodes must have an entry
  std::map<int, double> node_qty;

  /// whether a node is exclusive
  /// @warning all nodes must have an entry
  std::map<int, bool> node_excl;
 
  /// requester id : exclusive bid node ids
  /// @warning all request groups must have an entry
  std::map<int, std::vector<int> > excl_req_nodes;
 
  /// supplier id : all groupings of exclusive nodes
  /// exclusive node groups are representative of cases where multiple bids
  /// are represented by the same, quantized resource object (e.g., an assembly)
  /// @warning all supply groups must have an entry
  std::map<int, std::vector< std::vector<int> > > excl_sup_nodes;
  
  /// node : (arc : unit capacities)
  std::map<int, std::map<int, std::vector<double> > > node_ucaps;

  /// arc id : u_node id
  std::map<int, int> arc_to_unode;

  /// arc id : v_node id
  std::map<int, int> arc_to_vnode;

  /// the preference associated with an arc
  /// @warning all arcs must have an entry
  std::map<int, double> arc_pref;
};

/// constructs and runs a resource exchange
///
/// @param gparams all parameters required to construct the ExchangeGraph
/// @param sparams all parameters required to configure the ExchangeSolver
/// @return a Solution container
Solution execute_exchange(GraphParams& gparams, SolverParams& sparams);

/// std::vector<int> test();
std::vector<ArcFlow> test();

#endif // CYCLOPTS_EXECUTE_H_
