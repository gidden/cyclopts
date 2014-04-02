#include "execute.h"

#include <vector>
#include <math.h>
#include <cassert>
#include <algorithm>

#include <boost/math/special_functions/round.hpp>

#include "exchange_graph.h"
#include "prog_solver.h"

using namespace cyclus;

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

void add_requests(RequestParams& params,
                  ExchangeGraph& g, 
                  std::map<int, ExchangeNode::Ptr>& id_to_node,
                  std::map<int, RequestGroup::Ptr>& id_to_req_grp) {
  
  std::map<int, std::vector<int> >& req_grps = params.u_nodes_per_req;
  std::map<int, std::vector<int> >::iterator m_it;
  int grp_id;
  RequestGroup::Ptr rg;
  for (m_it = req_grps.begin(); m_it != req_grps.end(); ++m_it) {
    grp_id = m_it->first;
    rg = RequestGroup::Ptr(new RequestGroup(params.req_qty[grp_id]));
    id_to_req_grp[m_it->first] = rg;
    
    std::vector<int>& nodes = m_it->second;  
    int i;
    int node_id;
    ExchangeNode::Ptr n;
    for (i = 0; i != nodes.size(); i++) {
      node_id = nodes[i];
      n = ExchangeNode::Ptr(new ExchangeNode(params.u_node_qty[node_id],
                                             params.u_node_excl[node_id]));
      rg->AddExchangeNode(n);
      id_to_node[node_id] = n;
    }

    std::vector<double>& vals = params.constr_vals[grp_id];
    for (i = 0; i != vals.size(); i++) {
      rg->AddCapacity(vals[i]);
    }
    rg->AddCapacity(params.def_constr_val[grp_id]);
    g.AddRequestGroup(rg);
  }
  
}

void add_arcs(RequestParams& params,
              ExchangeGraph& g, 
              std::map<int, ExchangeNode::Ptr>& id_to_node,
              std::map<int, Arc>& id_to_arc) {
  
  std::map<int, int>& arc_to_unode = params.arc_to_unode;
  std::map<int, int>::iterator m_it;
  int u_id, v_id, a_id;
  ExchangeNode::Ptr u, v;
  for (m_it = arc_to_unode.begin(); m_it != arc_to_unode.end(); ++m_it) {
    a_id = m_it->first;
    u_id = m_it->second;
    v_id = params.arc_to_vnode[a_id];
    u = id_to_node[u_id];
    v = id_to_node[v_id];
    Arc a(u, v);
    id_to_arc[a_id] = a;
    u->unit_capacities[a] = params.node_ucaps[u_id][a_id];
    u->unit_capacities[a].push_back(params.def_constr_coeffs[u_id]); // @TODO confirm this is correct
    u->prefs[a] = params.arc_pref[a_id];
    v->unit_capacities[a] = params.node_ucaps[v_id][a_id];
  }
}

void execute_exchange(RequestParams& params, std::string db_path) {
  ProgSolver solver("cbc", true); 
  ExchangeGraph g;

  std::map<int, ExchangeNode::Ptr> id_to_node;
  std::map<int, RequestGroup::Ptr> id_to_req_grp;
  std::map<int, Arc> id_to_arc;

  add_requests(params, g, id_to_node, id_to_req_grp);
  add_arcs(params, g, id_to_node, id_to_arc);

  // // this belongs in the constraint addition
  // std::vector< std::vector<int> >& mutual_grps = params.mutual_req_grps[grp_id];
  // std::vector<ExchangeNode::Ptr> mutual_reqs;
  // int j;
  // for (i = 0; i != mutual_grps.size(); i++) {
  //   std::vector<int>& mutual_grp = mutual_grps[i];
  //   for (j = 0; j != mutual_grp.size(); j++) {
  //     node_id = mutual_grp[j];
  //     mutual_reqs.push_back(id_to_node[node_id]);
  //   }
  //   rg->AddMutualReqs(mutual_reqs);
  //   mutual_reqs.clear();
  // }
  
  // std::map<ExchangeNodeGroup::Ptr, int> supply_commods;
  // std::map<int, std::vector<ExchangeNodeGroup::Ptr> > supply_by_commods;

  // for (int i = 0; i != n_supply; i++) {
  //   std::vector<int> commod_subset = s.SampleSubsetAvgSize(n_commods,
  //                                                          avg_commod_sup);
  //   for (int j = 0; j != commod_subset.size(); j++) {
  //     ExchangeNodeGroup::Ptr sg(new ExchangeNodeGroup());
  //     g.AddSupplyGroup(sg);
  //     supply_commods[sg] = commod_subset[j];
  //     supply_by_commods[commod_subset[j]].push_back(sg);
  //   }
  // }  

  // for (int i = 0; i != n_commods; i++) {
  //   std::vector<ExchangeNode::Ptr>& reqs = reqs_by_commods[i];
  //   std::vector<ExchangeNodeGroup::Ptr>& sups = supply_by_commods[i];
  //   int N_arcs = boost::math::round(
  //       sups.size() * (reqs.size() - 1) * connect_prob + sups.size());

  //   std::vector< std::pair<ExchangeNode::Ptr, ExchangeNodeGroup::Ptr> >
  //       pairs = s.ReqArcs(reqs, sups, N_arcs);

  //   assert(pairs.size() == N_arcs);
    
  //   for (int j = 0; j != pairs.size(); j++) {
  //     ExchangeNode::Ptr sup(new ExchangeNode());
  //     pairs[j].second->AddExchangeNode(sup);
  //     Arc a(pairs[j].first, sup);
  //     g.AddArc(a);
  //   }
  // }
  
  solver.ExchangeSolver::Solve(&g);
}

void execute_exchange(SupplyParams& params, std::string db_path) {
  ProgSolver solver("cbc", true); 
  ExchangeGraph g;
  
  solver.ExchangeSolver::Solve(&g);
}
