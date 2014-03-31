#include "execute.h"

#include <vector>
#include <math.h>
#include <cassert>
#include <algorithm>

#include <boost/math/special_functions/round.hpp>

#include "exchange_graph.h"
#include "prog_solver.h"

#include "distributions.h"

using namespace cyclus;

int RequestRC::i() { return i_; }
int SupplyRC::i() { return i_; }

void test() {
  std::cout << "testing cyclopts!\n";
  
  ProgSolver s("cbc", true); 
  ExchangeGraph g;

  double qty, unit_cap_req, capacity, unit_cap_sup, flow;
  qty = 5;
  unit_cap_req = 1;
  capacity = 10;
  unit_cap_sup = 1;
  flow = qty;
  bool exclusive_orders = true;
  
  ExchangeNode::Ptr u(new ExchangeNode(qty, exclusive_orders));
  ExchangeNode::Ptr v(new ExchangeNode());
  Arc a(u, v);
  
  u->unit_capacities[a].push_back(unit_cap_req);
  u->prefs[a] = 1;
  v->unit_capacities[a].push_back(unit_cap_sup);
  
  RequestGroup::Ptr request(new RequestGroup(qty));
  request->AddCapacity(qty);
  request->AddExchangeNode(u);  
  g.AddRequestGroup(request);

  ExchangeNodeGroup::Ptr supply(new ExchangeNodeGroup());
  supply->AddCapacity(capacity);
  supply->AddExchangeNode(v);  
  g.AddSupplyGroup(supply);

  g.AddArc(a);

  s.ExchangeSolver::Solve(&g);
}

void run_rxtr_req(int n_supply,
                  int n_demand,
                  int dem_node_avg,
                  int n_commods,
                  int dem_commod_avg,
                  int avg_commod_sup,
                  double excl_prob,
                  double connect_prob,
                  int avg_sup_caps,
                  int avg_dem_caps) {
  ProgSolver solver("cbc", true); 
  ExchangeGraph g;

  Sampler s;

  std::map<ExchangeNode::Ptr, int> request_commods;
  std::map<int, std::vector<ExchangeNode::Ptr> > reqs_by_commods;
    
  for (int i = 0; i != n_demand; i++) {
    double amt = s.SampleReqAmt(); // total request amount
    RequestGroup::Ptr rg(new RequestGroup(amt));
    int n_nodes = s.SampleNNodes(dem_node_avg); // total number of request nodes in group
    std::vector<int> commods = s.SampleCommods(n_nodes, n_commods,
                                               dem_commod_avg); // assign commodity to each node
    for (int j = 0; j != n_nodes; j++) {
      // revisit this!
      ExchangeNode::Ptr n(new ExchangeNode(amt, s.SampleLinear(excl_prob))); // request node amt and exclusivity
      rg->AddExchangeNode(n);
      request_commods[n] = commods[j];
      reqs_by_commods[commods[j]].push_back(n);
    }
    g.AddRequestGroup(rg);
  }
  
  std::map<ExchangeNodeGroup::Ptr, int> supply_commods;
  std::map<int, std::vector<ExchangeNodeGroup::Ptr> > supply_by_commods;

  for (int i = 0; i != n_supply; i++) {
    std::vector<int> commod_subset = s.SampleSubsetAvgSize(n_commods,
                                                           avg_commod_sup);
    for (int j = 0; j != commod_subset.size(); j++) {
      ExchangeNodeGroup::Ptr sg(new ExchangeNodeGroup());
      g.AddSupplyGroup(sg);
      supply_commods[sg] = commod_subset[j];
      supply_by_commods[commod_subset[j]].push_back(sg);
    }
  }  

  for (int i = 0; i != n_commods; i++) {
    std::vector<ExchangeNode::Ptr>& reqs = reqs_by_commods[i];
    std::vector<ExchangeNodeGroup::Ptr>& sups = supply_by_commods[i];
    int N_arcs = boost::math::round(
        sups.size() * (reqs.size() - 1) * connect_prob + sups.size());

    std::vector< std::pair<ExchangeNode::Ptr, ExchangeNodeGroup::Ptr> >
        pairs = s.ReqArcs(reqs, sups, N_arcs);

    assert(pairs.size() == N_arcs);
    
    for (int j = 0; j != pairs.size(); j++) {
      ExchangeNode::Ptr sup(new ExchangeNode());
      pairs[j].second->AddExchangeNode(sup);
      Arc a(pairs[j].first, sup);
      g.AddArc(a);
    }
  }
  
  solver.ExchangeSolver::Solve(&g);
}
