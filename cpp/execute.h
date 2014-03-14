#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

/// constructs and runs a reactor-request resource exchange
///
/// @param n_supply the number of supplier node groups
/// @param n_consume the number of consumer node groups
/// @param con_node_avg the average number of consumer nodes in a group
/// @param n_commods the number of commodities
/// @param con_commod_avg the average number of commodities in a consumer node
/// group
/// @param avg_commod_sup the average number of commodities that a supplier
/// can supply (i.e., supply node groups per supplier)
/// @param excl_prob the probability that a consumer node will be exclusive
/// @param connect_prob the probability that a connection is made between a
/// request and supply of the same commodity
/// @param avg_sup_caps average number of supply capacities per group
/// @param avg_sup_caps average number of demand capacities per group
void run_rxtr_req(int n_supply = 1,
                  int n_consume = 1,
                  int con_node_avg = 1,
                  int n_commods = 1,
                  int con_commod_avg = 1,
                  int avg_commod_sup = 1,
                  double excl_prob = 0.0,
                  double connect_prob = 1.0,
                  int avg_sup_caps = 1,
                  int avg_dem_caps = 1);

void test();

#endif // CYCLOPTS_EXECUTE_H_
