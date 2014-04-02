from __future__ import print_function

import cyclopts

# from cyclopts.execute import run_rxtr_req
from cyclopts.execute import test
# from cyclopts.execute import SupplyRC
# from cyclopts.execute import Distribution
# from cyclopts.execute import AssemblyParam
# from cyclopts.execute import AssemblyParam

def main():
    test()
    # rc = SupplyRC()
    # # dist = Distribution(1)
    # # param = AssemblyParam()
    # run_rxtr_req(rc)
    # print("rc's i:", rc.i())
    # return rc.i()
    return 0

if __name__ == "__main__":
    main()
