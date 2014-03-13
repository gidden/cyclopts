#ifndef CYCLOPTS_EXECUTE_H_
#define CYCLOPTS_EXECUTE_H_

/// constructs and runs a reactor-request resource exchange
///
/// @param n_supply the number of supplier node groups
/// @param n_consume the number of consumer node groups
/// @param con_node_avg the average number of consumer nodes in a group
/// @param n_commod the number of commodities
/// @param con_commod_avg the average number of commodities in a consumer node
/// group
/// @param excl_prob the probability that a consumer node will be exclusive
/// @param connect_prob the probability that a connection is made between a
/// request and supply of the same commodity
void run_rxtr_req(int n_supply = 1,
                  int n_consume = 1,
                  int con_node_avg = 1,
                  int n_commod = 1,
                  int con_commod_avg = 1,
                  double excl_prob = 0.0,
                  double connect_prob = 1.0);

#endif // CYCLOPTS_EXECUTE_H_
