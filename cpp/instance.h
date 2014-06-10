#include <vector>

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNodeGroup
class ExGroup {
 public:
  ExGroup(int id, bool kind, std::vector<double>& ucaps, double qty=0)
    : id(id),
      kind(kind),
      caps(caps),
      qty(qty) { };

  int id;  
  // 0 == request, 1 == supply
  bool kind;
  double qty;
  std::vector<double> caps;
};

/// A struct of POD and STL of PODs representation of a Cyclus ExchangeNode
class ExNode {
 public:
  ExNode(int id, bool kind, int gid, std::vector<double>& ucaps,
       bool excl=false, double qty=0)
    : id(id),
      kind(kind),
      gid(gid),
      ucaps(ucaps),
      excl(excl),
      qty(qty) { };
  
  int id;
  // group id
  int gid;
  // 0 == supply, 1 == request
  bool kind;
  bool excl;
  double qty;
  std::vector<double> ucaps;
};

/// A struct of POD and STL of PODs representation of a Cyclus Arc
class ExArc {
 public:
  ExArc(int uid, int vid, double pref)
    : uid(uid),
      vid(vid),
      pref(pref),
      flow(0) { };

  // u == supply
  int uid;
  // v == request
  int vid;
  double pref, flow;
};

/// A container class for all parameters required to construct an instance of a
/// Cyclus ExchangeSolver.
class ExSolver {
 public:
  ExSolver(std::string type = "cbc") : type(type) {};
  std::string type;
};

/// A simple container class for exchange solutions.
///
/// ArcFlows are included for all arcs and the solution time is reported in
/// microseconds.
class ExSolution {
 public:
  std::vector<ExArc> flows;
  double time; // in s
  std::string cyclus_version;

  Solution() { };
  
  Solution(const Solution& other) :
      flows(other.flows), time(other.time), cyclus_version(other.cyclus_version)
      { };
};

/// constructs and runs a resource exchange
ExSolution run(std::vector<Group>& groups, std::vector<Node>& nodes,
               std::vector<Arc>& arcs, ExSolver solver);
