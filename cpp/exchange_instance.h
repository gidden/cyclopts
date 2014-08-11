#ifndef CYCLOPTS_INSTANCE_H_
#define CYCLOPTS_INSTANCE_H_

#include <vector>
#include <string>
#include <utility>
#include <map>

namespace cyclopts {

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNodeGroup
class ExGroup {
 public:
  ExGroup() {};
  ExGroup(int id, bool kind, std::vector<double>& caps, double qty = 0)
    : id(id),
      kind(kind),
      caps(caps),
      qty(qty) { };
  ExGroup(const ExGroup& other)
    : id(other.id),
      kind(other.kind),
      caps(other.caps),
      qty(other.qty) { };

  int id;  
  bool kind; // true == request, false == bid
  double qty;
  std::vector<double> caps;
};

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNode
class ExNode {
 public:
  ExNode() {};
  ExNode(int id, int gid, bool kind, double qty = 0,
         bool excl=false, int excl_id = -1)
    : id(id),
      gid(gid),
      kind(kind),
      qty(qty),
      excl(excl),
      excl_id(excl_id)  { };
  ExNode(const ExNode& other)
    : id(other.id),
      gid(other.gid),
      kind(other.kind),
      qty(other.qty),
      excl(other.excl),
      excl_id(other.excl_id)  { };
  
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
  ExArc() {};
  ExArc(int id,
        int uid, std::vector<double>& ucaps,
        int vid, std::vector<double>& vcaps,
        double pref)
    : id(id),
      uid(uid),
      ucaps(ucaps),
      vid(vid),
      vcaps(vcaps),
      pref(pref) { };
  ExArc(const ExArc& other)
    : id(other.id),
      uid(other.uid),
      ucaps(other.ucaps),
      vid(other.vid),
      vcaps(other.vcaps),
      pref(other.pref) { };

  inline bool operator<(const ExArc& other) const {
    return id < other.id;
  }

  int id;
  int uid; // u == request
  std::vector<double> ucaps;
  int vid; // v == bid
  std::vector<double> vcaps;
  double pref;
};

/// A container class for all parameters required to construct an instance of a
/// Cyclus ExchangeSolver.
class ExSolver {
 public:
  explicit ExSolver(std::string type = "cbc") : type(type) { };
  std::string type;
};

/// a generic container for problem instance solutions
class ProbSolution {
 public:
  ProbSolution(double time = 0, double objective = 0, std::string type = "",
               std::string cyclus_version = "")
    : time(time),
      objective(objective), 
      type(type),
      cyclus_version(cyclus_version) { };
  
  double time;
  double objective;
  std::string type;
  std::string cyclus_version;
};

/// A simple container class for exchange solutions.
class ExSolution: public ProbSolution {
 public:
  ExSolution(double time = 0, double objective = 0, std::string type = "",
             std::string cyclus_version = "")
    : ProbSolution(time, objective, type, cyclus_version) { };
  std::map<int, double> flows;
  double pref_flow; // sum (preferences * flow) 
};

ExSolution Run(std::vector<ExGroup>& groups, std::vector<ExNode>& nodes,
               std::vector<ExArc>& arcs, ExSolver& solver, bool verbose=false);

} // namespace cyclopts

#endif // CYCLOPTS_INSTANCE_H_
