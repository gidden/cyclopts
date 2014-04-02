#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

#include <string>
#include <map>
#include <vector>

struct RequestParams {
  /// requester : their request nodes
  std::map<int, std::vector<int> > u_nodes_per_req;

  /// requester : request qty
  std::map<int, double> req_qty;

  /// request node to request amount
  /// @warning all request nodes must have an entry
  std::map<int, double> u_node_qty;
  
  /// whether a request is exclusive
  /// @warning all request nodes must have an entry
  std::map<int, bool> u_node_excl;
  
  /// requester : groupings of nodes (assemblies) that meet the same demand
  /// @warning all request groups must have an entry
  std::map<int, std::vector< std::vector<int> > > mutual_req_grps;
  
  /// requester : the average quantity of mutual request groups
  /// @warning all request groups must have an entry
  /// @warning the ordering of vector entries must follow mutual_req_grps
  std::map<int, std::vector<int> > mutual_req_avg_qty;

  /// /// request node to commodity
  /// std::map<int, int> u_node_commods;

  /// std::map<int, std::map<int, std::vector<double> > > node_ucaps;
};

struct SupplyParams {
  std::map<int, double> node_qtys;
  /// std::map<int, std::map<int, std::vector<double> > > node_ucaps;
};
  
/// constructs and runs a reactor-request-based resource exchange
///
/// @param params all exchange parameters
/// @param db_path the path to the output database to use
void execute_exchange(RequestParams& params, std::string db_path);

/// constructs and runs a reactor-supply-based resource exchange
///
/// @param params all exchange parameters
/// @param db_path the path to the output database to use
void execute_exchange(SupplyParams& params, std::string db_path);

void test();

#endif // CYCLOPTS_EXECUTE_H_
