#ifndef CYCLOPTS_INSTANCE_H_
#define CYCLOPTS_INSTANCE_H_

#include <vector>
#include <string>

namespace cyclopts {

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNodeGroup
class ExGroup {
 public:
  ExGroup(int id, bool kind, std::vector<double>& ucaps, double qty = 0)
    : id(id),
      kind(kind),
      caps(caps),
      qty(qty) { };

  int id;  
  bool kind; // true == request, false == bid
  double qty;
  std::vector<double> caps;
};

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNode
class ExNode {
 public:
  ExNode(int id, int gid, bool kind, double qty = 0,
         bool excl=false, int excl_id = 0)
    : id(id),
      gid(gid),
      kind(kind),
      qty(qty),
      excl(excl),
      excl_id(excl_id)  { };
  
  int id;
  int gid; // group id
  bool kind; // true == request, false == bid
  double qty;
  bool excl;
  /// for grouping exclusive nodes, e.g., used assembly bids. any value > 0 will
  /// add an exclusivity constraint for all arcs of all nodes that share the same
  /// gid and excl_id
  /// @warning a request node should NOT have an exclusive id, they should
  /// only have excl == true
  int excl_id; 
};

/// A struct of POD and STL of PODs representation of a Cyclus Arc
class ExArc {
 public:
  ExArc(int uid, std::vector<double>& ucaps,
        int vid, std::vector<double>& vcaps,
        double pref)
    : uid(uid),
      ucaps(ucaps),
      vid(vid),
      vcaps(vcaps),
      pref(pref),
      flow(0) { };

  inline bool operator<(const ExArc& other) const {
    return uid < other.uid && vid < other.vid;
  }
  
  int uid; // u == request
  std::vector<double> ucaps;
  int vid; // v == bid
  std::vector<double> vcaps;
  double pref, flow;
};

/// A container class for all parameters required to construct an instance of a
/// Cyclus ExchangeSolver.
class ExSolver {
 public:
  explicit ExSolver(std::string type = "cbc") : type(type) { };
  std::string type;
};

/// A simple container class for exchange solutions.
class ExSolution {
 public:
  ExSolution(double time, std::string cyclus_version)
      : time(time), cyclus_version(cyclus_version) { };
  
  double time; // unit: s
  std::string cyclus_version;
};

/// constructs and runs a resource exchange
ExSolution Run(std::vector<ExGroup>& groups, std::vector<ExNode>& nodes,
               std::vector<ExArc>& arcs, ExSolver& solver);

} // namespace cyclopts

#endif // CYCLOPTS_INSTANCE_H_
