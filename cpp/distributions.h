#ifndef CYCLOPTS_GENERATOR_H_
#define CYCLOPTS_GENERATOR_H_

#include <string>
#include <vector>

#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int.hpp>
#include <boost/random/variate_generator.hpp>
#include <boost/random/uniform_real.hpp>

#include "exchange_graph.h"

class Sampler {
 public:
  Sampler() {};

  double SampleReqAmt() { return 10.0; }

  int SampleNNodes(int avg) { return avg; }

  /// generates a commodity index vector.
  ///
  /// @param size the size of vector to return
  /// @param n_commods the total number of possible commodity indicies
  /// @param commod_avg the average number of commodities in a grouping
  /// @returns a commodity index vector
  std::vector<int> SampleCommods(int size, int n_commods, int commod_avg) {
    std::vector<int> v;
    for (int i = 0; i != size; i++) {
      v.push_back(n_commods); // do logic here
    }
    return v;
  }

  /// generates a random subset of indicies
  ///
  /// @param n the super set size
  /// @param avg size of the subset
  /// @returns a subset of the commodity indicies
  std::vector<int> SampleSubsetAvgSize(int n, int avg) {
    std::vector<int> v;
    for (int i = 0; i != avg; i++) { // do logic here
      v.push_back(i); 
    }
    return v;
  }

  /// @returns true if sampled value in [0, 1] is < prob
  bool SampleLinear(double prob) {   
    boost::uniform_real<> dist(0, 1);
    return prob > dist(rng_);
  }

  /// generates a random subset of indicies
  ///
  /// @param n the super set size
  /// @param avg size of the subset
  /// @returns a subset of the commodity indicies
  std::vector<int> SampleSubsetProb(int n, double prob) {
    std::vector<int> v;
    for (int i = 0; i != n; i++) { // do logic here
      if (SampleLinear(prob)) v.push_back(i);
    }
    return v;
  }

  /// returns a random set of request-node, supply-group pairings with size
  /// equal to N
  ///
  /// @param reqs all request nodes that could possibly be connected with a
  /// supply group
  /// @param sups all supply node groups that could be connected with a request
  /// node in reqs
  /// @param N the total number of connections to be made
  std::vector< std::pair<cyclus::ExchangeNode::Ptr, cyclus::ExchangeNodeGroup::Ptr> >
      ReqArcs(std::vector<cyclus::ExchangeNode::Ptr>& reqs,
              std::vector<cyclus::ExchangeNodeGroup::Ptr>& sups,
              int N) {
    
    std::vector< std::pair<cyclus::ExchangeNode::Ptr,
        cyclus::ExchangeNodeGroup::Ptr> > pairs;
    for (int j = 0; j != reqs.size(); j++) {
      for (int k = 0; k != sups.size(); k++) {
        pairs.push_back(std::make_pair(reqs[j], sups[k]));
      }
    }

    boost::uniform_int<> uni_dist;
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> >
        rand_num(rng_, uni_dist);
    std::random_shuffle(pairs.begin(), pairs.end(), rand_num);

    return std::vector< std::pair<cyclus::ExchangeNode::Ptr,
        cyclus::ExchangeNodeGroup::Ptr> > (pairs.begin(), pairs.begin() + N);
  }
  
 private:
  boost::mt19937 rng_;
};

#endif // CYCLOPTS_GENERATOR_H_
