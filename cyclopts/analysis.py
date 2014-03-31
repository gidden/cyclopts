from __future__ import print_function

from cyclopts.execute import run_rxtr_req
from cyclopts.execute import test
from cyclopts.execute import SupplyRC

def main():
    test()
    rc = SupplyRC()
    print("rc's i:", rc.i())

if __name__ == "__main__":
    main()
