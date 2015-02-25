#include "exchange_instance.h"

#include <stdexcept>

#include "exchange_graph.h"
#include "greedy_solver.h"
#include "prog_solver.h"
#include "version.h"
#include "capacity_types.h"

#include "cpu_time.h"

namespace cyclopts {

struct ExXlationCtx {
  std::map<int, cyclus::ExchangeNode::Ptr> id_to_node;
  std::map<int, cyclus::ExchangeNodeGroup::Ptr> id_to_grp;
  std::map<ExArc, cyclus::Arc> arc_map;
};

void AddGroups(std::vector<ExGroup>& groups,
               ExXlationCtx& ctx,
               cyclus::ExchangeGraph& g) {
  std::vector<ExGroup>::iterator git;
  cyclus::RequestGroup::Ptr rg;
  cyclus::ExchangeNodeGroup::Ptr bg;
  for (git = groups.begin(); git != groups.end(); ++git) {
    if (git->kind) { // true == request
      rg = cyclus::RequestGroup::Ptr(new cyclus::RequestGroup(git->qty));
      g.AddRequestGroup(rg);
      bg = rg;
    } else { // false == bid
      bg = cyclus::ExchangeNodeGroup::Ptr(new cyclus::ExchangeNodeGroup());
      g.AddSupplyGroup(bg);
    }
    ctx.id_to_grp[git->id] = bg;
    cyclus::cap_t t;
    int i;
    for (i = 0; i < git->caps.size(); ++i) {
      t = git->cap_dirs[i] == 1 ? cyclus::GTEQ : cyclus::LTEQ;
      bg->AddCapacity(git->caps[i], t);
    }
  }
}

void AddNodes(std::vector<ExNode>& nodes,
              ExXlationCtx& ctx,
              cyclus::ExchangeGraph& g) {
  cyclus::ExchangeNode::Ptr n;
  cyclus::ExchangeNodeGroup::Ptr grp;
  // mapping group id and excl set id to the collection of nodes
  std::map<std::pair<int, int>,
           std::vector<cyclus::ExchangeNode::Ptr> > excl_grps; 

  std::vector<ExNode>::iterator nit;
  for (nit = nodes.begin(); nit != nodes.end(); ++nit) {
    n = cyclus::ExchangeNode::Ptr(
        new cyclus::ExchangeNode(nit->qty, nit->excl));
    grp = ctx.id_to_grp[nit->gid];
    grp->AddExchangeNode(n);
    ctx.id_to_node[nit->id] = n;
    if (nit->excl_id > 0) {
      excl_grps[std::make_pair(nit->gid, nit->excl_id)].push_back(n);
    }
  }

  std::map<std::pair<int, int>,
           std::vector<cyclus::ExchangeNode::Ptr> >::iterator git;
  for (git = excl_grps.begin(); git != excl_grps.end(); ++git) {
    grp = ctx.id_to_grp[git->first.first];
    grp->AddExclGroup(git->second);
  }
}    

void AddArcs(std::vector<ExArc>& arcs,
             ExXlationCtx& ctx,
             cyclus::ExchangeGraph& g) {
  std::vector<ExArc>::iterator ait;
  cyclus::ExchangeNode::Ptr u, v;
  for (ait = arcs.begin(); ait != arcs.end(); ++ait) {
    u = ctx.id_to_node[ait->uid];
    v = ctx.id_to_node[ait->vid];
    cyclus::Arc a(u, v);
    g.AddArc(a);
    ctx.arc_map[*ait] = a;
    u->unit_capacities[a] = ait->ucaps;
    u->prefs[a] = ait->pref;
    v->unit_capacities[a] = ait->vcaps;
  }
}

cyclus::ExchangeSolver* SolverFactory(Solver& solver) {
  std::string type = solver.type == "" ? "cbc" : solver.type;
  cyclus::ExchangeSolver* ret;
  bool excl_orders = true;
  if (type == "cbc")
    ret = new cyclus::ProgSolver(type, excl_orders);
  else if (type == "clp")
    ret = new cyclus::ProgSolver(type, !excl_orders);
  else if (type == "clp-e")
    ret = new cyclus::ProgSolver("clp", excl_orders);
  else if (type == "greedy")
    ret = new cyclus::GreedySolver(excl_orders);
  else
    throw std::invalid_argument("Invalid solver type " + solver.type);
  return ret;
}

ExSolution Run(std::vector<ExGroup>& groups, std::vector<ExNode>& nodes,
               std::vector<ExArc>& arcs, Solver& solver, bool verbose) {
  ExXlationCtx ctx;
  cyclus::ExchangeGraph g;

  // construct
  AddGroups(groups, ctx, g);
  AddNodes(nodes, ctx, g);
  AddArcs(arcs, ctx, g);
  
  // solve and get time
  cyclus::ExchangeSolver* s = SolverFactory(solver);
  if (verbose)
    s->verbose();
  double start, stop;
  // start = getCPUTime();
  start = CoinCpuTime();
  double obj = s->cyclus::ExchangeSolver::Solve(&g);
  // stop = getCPUTime();
  stop = CoinCpuTime();
  double dur = stop - start; // in seconds
  delete  s;
  std::string type = "ResourceExchange";
  ExSolution soln(dur, obj, type, cyclus::version::describe());

  // update flows on ExArcs
  const std::vector<cyclus::Match>& matches = g.matches();
  std::map<cyclus::Arc, double> flows;
  for (int i = 0; i != matches.size(); i++) {
    flows.insert(matches[i]);
  }
  std::vector<ExArc>::iterator ait;
  for (ait = arcs.begin(); ait != arcs.end(); ++ait) {
    ExArc& exa = *ait;
    double flow = flows[ctx.arc_map[exa]];
    soln.flows[exa.id] = flow;
    soln.pref_flow += exa.pref * flow;
    soln.cost_flow += 1 / exa.pref * flow;
  }

  return soln;
}

} // namespace cyclopts
