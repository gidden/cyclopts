#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

#include <string>
#include <map>
#include <vector>

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

class ExecParams {
 public:  
  /// requester : their request nodes
  std::map<int, std::vector<int> > u_nodes_per_req;

  /// supplier : their supply nodes
  std::map<int, std::vector<int> > v_nodes_per_sup;

  /// requester : request qty
  std::map<int, double> req_qty;

  /// node id to node quantity
  /// @warning all nodes must have an entry
  std::map<int, double> node_qty;

  /// whether a node is exclusive
  /// @warning all nodes must have an entry
  std::map<int, bool> node_excl;

  /// requester id : all groupings of exclusive nodes
  /// @warning all request groups must have an entry
  std::map<int, std::vector< std::vector<int> > > excl_req_nodes;
 
  /// supplier id : exclusive bid node ids
  /// @warning all supply groups must have an entry
  std::map<int, std::vector<int> > excl_sup_nodes;
  
  /// node : (arc : unit capacities)
  std::map<int, std::map<int, std::vector<double> > > node_ucaps;

  /// requester or supplier : constraint rhs values 
  /// @warning all groups must have an entry
  std::map<int, std::vector<double> > constr_vals;

  /// request node : the default mass constraint coefficient
  /// note this is how multicommodity requests are taken into account
  /// @warning all request nodes must have an entry
  std::map<int, double> def_constr_coeffs;

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
/// @param params all exchange parameters
/// @param db_path the path to the output database to use
std::vector<ArcFlow> execute_exchange(ExecParams& params, std::string db_path = "");
/// void execute_exchange(ExecParams& params, std::string db_path = "");

/// std::vector<int> test();
std::vector<ArcFlow> test();

#endif // CYCLOPTS_EXECUTE_H_
