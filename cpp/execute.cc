#include "execute.h"

#include <vector>
#include <limits>
#include <math.h>
#include <cassert>
#include <algorithm>
#include <time.h>

#include <boost/lexical_cast.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>

#include "exchange_graph.h"
#include "greedy_solver.h"
#include "prog_solver.h"
#include "version.h"

#include "cpu_time.h"

using namespace cyclus;

GraphParams::GraphParams() {
  boost::uuids::uuid uuid = boost::uuids::random_generator()();
  id = boost::lexical_cast<std::string>(uuid);
}

void GraphParams::AddRequestGroup(int g) {
  u_nodes_per_req[g] = std::vector<int>();
  req_qty[g] = 0;
  excl_req_nodes[g] = std::vector<int>();
  constr_vals[g] = std::vector<double>();
}

void GraphParams::AddRequestNode(int n, int g) {
  node_qty[n] = 1;
  node_excl[n] = false;
  node_ucaps[n] = std::map<int, std::vector<double> >();
  def_constr_coeff[n] = 0;
  u_nodes_per_req[g].push_back(n);
}

void GraphParams::AddSupplyGroup(int g) {
  v_nodes_per_sup[g] = std::vector<int>();
  excl_sup_nodes[g] = std::vector< std::vector<int> >();
  constr_vals[g] = std::vector<double>();
}

void GraphParams::AddSupplyNode(int n, int g) {
  node_qty[n] = std::numeric_limits<double>::max(); // node flow upper bound
  node_excl[n] = false;
  node_ucaps[n] = std::map<int, std::vector<double> >();
  v_nodes_per_sup[g].push_back(n);
}

struct ExecContext {  
  std::map<int, ExchangeNode::Ptr> id_to_node;
  std::map<int, RequestGroup::Ptr> id_to_req_grp;
  std::map<int, ExchangeNodeGroup::Ptr> id_to_sup_grp;
  std::map<int, Arc> id_to_arc;
  std::map<Arc, int> arc_to_id;
};

void add_requests(GraphParams& params, ExchangeGraph& g, ExecContext& ctx) {
  
  std::map<int, std::vector<int> >& req_grps = params.u_nodes_per_req;
  std::map<int, std::vector<int> >::iterator rg_it;
  RequestGroup::Ptr rg;
  ExchangeNode::Ptr n;
  int i, g_id, n_id;
  for (rg_it = req_grps.begin(); rg_it != req_grps.end(); ++rg_it) {
    // make group
    g_id = rg_it->first;
    rg = RequestGroup::Ptr(new RequestGroup(params.req_qty[g_id]));
    ctx.id_to_req_grp[g_id] = rg;

    // add nodes
    std::vector<int>& nodes = rg_it->second;  
    for (i = 0; i != nodes.size(); i++) {
      n_id = nodes[i];
      n = ExchangeNode::Ptr(new ExchangeNode(params.node_qty[n_id],
                                             params.node_excl[n_id]));
      rg->AddExchangeNode(n);
      ctx.id_to_node[n_id] = n;
    }

    // add exclusive request groups
    std::vector<int>& ids = params.excl_req_nodes[g_id];
    for (i = 0; i != ids.size(); i++) {
      rg->AddExclNode(ctx.id_to_node[ids[i]]);
    }  

    // add constraint rhs
    std::vector<double>& vals = params.constr_vals[g_id];
    for (i = 0; i != vals.size(); i++) {
      rg->AddCapacity(vals[i]);
    }
    // add default constraint rhs
    rg->AddCapacity(params.req_qty[g_id]);

    // add group
    g.AddRequestGroup(rg);
  }

}

/// adds all supply groups and nodes to the graph and populates supply-id
/// mappings
void add_supply(GraphParams& params, ExchangeGraph& g, ExecContext& ctx) {  
  std::map<int, std::vector<int> >& sup_grps = params.v_nodes_per_sup;
  std::map<int, std::vector<int> >::iterator sg_it;
  ExchangeNodeGroup::Ptr sg;
  ExchangeNode::Ptr n;
  std::vector<ExchangeNode::Ptr> excl_grp;
  int i, j, g_id, n_id;
  for (sg_it = sup_grps.begin(); sg_it != sup_grps.end(); ++sg_it) {
    // make group
    g_id = sg_it->first;
    sg = ExchangeNodeGroup::Ptr(new ExchangeNodeGroup());
    ctx.id_to_sup_grp[g_id] = sg;
    
    // add nodes to group
    std::vector<int>& nodes = sg_it->second;  
    for (i = 0; i != nodes.size(); i++) {
      n_id = nodes[i];
      n = ExchangeNode::Ptr(new ExchangeNode(params.node_qty[n_id],
                                             params.node_excl[n_id]));
      sg->AddExchangeNode(n);
      ctx.id_to_node[n_id] = n;
    }

    // add exclusive bid nodes
    std::vector< std::vector<int> >& excl_nodes = params.excl_sup_nodes[g_id];
    for (i = 0; i != excl_nodes.size(); i++) {
      std::vector<int>& ids = excl_nodes[i];
      for (j = 0; j != ids.size(); j++) {
        excl_grp.push_back(ctx.id_to_node[ids[j]]);
      }
      sg->AddExclGroup(excl_grp);
      excl_grp.clear();
    }  


    // add constraint rhs
    std::vector<double>& vals = params.constr_vals[g_id];
    for (i = 0; i != vals.size(); i++) {
      sg->AddCapacity(vals[i]);
    }

    // add group
    g.AddSupplyGroup(sg);
  }  
}

/// adds all arcs to the exchange graph and populates id-arc mappings
void add_arcs(GraphParams& params, ExchangeGraph& g, ExecContext& ctx) {
  
  std::map<int, int>& arc_to_unode = params.arc_to_unode;
  std::map<int, int>::iterator it;
  int a_id, u_id, v_id;
  ExchangeNode::Ptr u, v;
  for (it = arc_to_unode.begin(); it != arc_to_unode.end(); ++it) {
    a_id = it->first;
    u_id = it->second;
    v_id = params.arc_to_vnode[a_id];
    u = ctx.id_to_node[u_id];
    v = ctx.id_to_node[v_id];

    // add arc
    Arc a(u, v);
    g.AddArc(a);
    ctx.id_to_arc[a_id] = a;
    ctx.arc_to_id[a] = a_id;

    // add unit capacities and preferences
    u->unit_capacities[a] = params.node_ucaps[u_id][a_id];
    // @TODO confirm this is correct
    u->unit_capacities[a].push_back(params.def_constr_coeff[u_id]); 
    u->prefs[a] = params.arc_pref[a_id];
    v->unit_capacities[a] = params.node_ucaps[v_id][a_id];
  }
}

/// factory method to provide an exchange solver
ExchangeSolver* get_solver(SolverParams& sparams) {
  std::string type = sparams.type == "" ? "cbc" : sparams.type;

  ExchangeSolver* ret;
  if (type == "cbc" || type == "clp") {
    ret = new ProgSolver(type, true);
  } else {
    ret = new GreedySolver(true);
  }
  return ret;
}

Solution execute_exchange(GraphParams& gparams, SolverParams& sparams) {
  ExchangeSolver* solver = get_solver(sparams);
  ExchangeGraph g;
  ExecContext ctx;
  
  add_requests(gparams, g, ctx);
  add_supply(gparams, g, ctx);
  add_arcs(gparams, g, ctx);

  double start, stop;
  start = getCPUTime();
  solver->ExchangeSolver::Solve(&g);
  stop = getCPUTime();
  double dur = stop - start; // in seconds
  
  const std::vector<Match>& matches = g.matches();
  Solution s;
  for (int i = 0; i != matches.size(); i++) {
    s.flows.push_back(ArcFlow(ctx.arc_to_id[matches[i].first],
                              matches[i].second));
  }
  s.time = dur;
  s.cyclus_version = cyclus::version::core();

  delete solver;
  
  return s;
}

// std::vector<int> test() {
std::vector<ArcFlow> test() {
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
  
  // std::vector<int> flows;
  std::vector<ArcFlow> flows;
  for (int i = 0; i != g.matches().size(); i++) {
    std::cout << "Adding arc\n";
    std::cout << "        i: " << i << "\n";
    std::cout << "     flow: " << g.matches()[i].second << "\n";
    flows.push_back(ArcFlow(i, g.matches()[i].second));
  }
  flows.push_back(ArcFlow(99, 4.5)); // for example purposes
  // flows.push_back(1);
  // flows.push_back(99);
  return flows;
}
