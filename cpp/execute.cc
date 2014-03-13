#include "execute.h"

#include "exchange_graph.h"
#include "prog_solver.h"

void run_rxtr_req(int n_supply,
                  int n_consume,
                  int con_node_avg,
                  int n_commod,
                  int con_commod_avg,
                  double excl_prob,
                  double connect_prob) {
  cyclus::ProgSolver s("cbc", true); 
  cyclus::ExchangeGraph g;
  s.Solve(g);  
}
