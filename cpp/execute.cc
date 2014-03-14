#include "execute.h"

#include <vector>

#include "exchange_graph.h"
#include "prog_solver.h"

#include "distributions.h"

using namespace cyclus;

void test() {
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
  std::map<int, std::vector<ExchangeNode::Ptr> > request_by_commods;
    
  for (int i = 0; i != n_demand; i++) {
    double amt = s.SampleReqAmt();
    RequestGroup::Ptr rg(new RequestGroup(amt));
    int n_nodes = s.SampleNNodes(dem_node_avg);
    std::vector<int> commods = s.SampleCommods(n_nodes, n_commods,
                                               dem_commod_avg);
    for (int j = 0; j != n_nodes; j++) {
      ExchangeNode::Ptr n(new ExchangeNode(amt, s.SampleLinear(excl_prob))); // revisit this!
      rg->AddExchangeNode(n);
      request_commods[n] = commods[j];
      request_by_commods[commods[j]].push_back(n);
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
      std::vector<ExchangeNode::Ptr>& nodes = request_by_commods[commod_subset[j]];
      std::vector<int> subset_indicies = s.SampleSubsetProb(nodes.size(),
                                                            connect_prob);
      for (int k = 0; k != subset_indicies.size(); k++) {
        ExchangeNode::Ptr sup(new ExchangeNode());
        ExchangeNode::Ptr req = nodes[k];
        Arc a(req, sup);
        sg->AddExchangeNode(sup);
        g.AddArc(a);
      }
      g.AddSupplyGroup(sg);
      supply_commods[sg] = commod_subset[j];
      supply_by_commods[commod_subset[j]].push_back(sg);
    }
  }  
  
  solver.ExchangeSolver::Solve(&g);
}
