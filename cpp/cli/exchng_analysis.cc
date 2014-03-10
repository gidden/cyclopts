
#include <iostream>

#include "bid.h"

#include "distributions.h"

int main(int argc, char* argv[]) {

  Generator gen;

  std::cout << "hi! " << gen.type() << "\n";
  
  return 0;
}

