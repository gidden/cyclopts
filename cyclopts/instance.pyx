################################################
#                 WARNING!                     #
# This file has been auto-generated by xdress. #
# Do not modify!!!                             #
#                                              #
#                                              #
#                    Come on, guys. I mean it! #
################################################
"""
"""
cimport cpp_instance
cimport dtypes
cimport instance
cimport numpy as np
cimport stlcontainers
from cyclopts cimport cpp_instance
from libc.stdlib cimport free
from libcpp cimport bool as cpp_bool
from libcpp.map cimport map as cpp_map
from libcpp.string cimport string as std_string
from libcpp.vector cimport vector as cpp_vector

import collections
import dtypes
import numpy as np
import stlcontainers

np.import_array()



cdef class ProbSolution:
    """no docstring for {'tarbase': 'instance', 'tarname': 'ProbSolution', 'language': 'c++', 'srcname': 'ProbSolution', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults


    def __init__(self, time=0, objective=0, type='', cyclus_version=''):
        """ProbSolution(self, time=0, objective=0, type='', cyclus_version='')
        """
        cdef char * type_proxy
        cdef char * cyclus_version_proxy
        type_bytes = type.encode()
        cyclus_version_bytes = cyclus_version.encode()
        self._inst = new cpp_instance.ProbSolution(<double> time, <double> objective, std_string(<char *> type_bytes), std_string(<char *> cyclus_version_bytes))
    
    
    def __dealloc__(self):
        if self._free_inst and self._inst is not NULL:
            free(self._inst)

    # attributes
    property cyclus_version:
        """no docstring for cyclus_version, please file a bug report!"""
        def __get__(self):
            return bytes(<char *> (<cpp_instance.ProbSolution *> self._inst).cyclus_version.c_str()).decode()
    
        def __set__(self, value):
            cdef char * value_proxy
            value_bytes = value.encode()
            (<cpp_instance.ProbSolution *> self._inst).cyclus_version = std_string(<char *> value_bytes)
    
    
    property objective:
        """no docstring for objective, please file a bug report!"""
        def __get__(self):
            return float((<cpp_instance.ProbSolution *> self._inst).objective)
    
        def __set__(self, value):
            (<cpp_instance.ProbSolution *> self._inst).objective = <double> value
    
    
    property time:
        """no docstring for time, please file a bug report!"""
        def __get__(self):
            return float((<cpp_instance.ProbSolution *> self._inst).time)
    
        def __set__(self, value):
            (<cpp_instance.ProbSolution *> self._inst).time = <double> value
    
    
    property type:
        """no docstring for type, please file a bug report!"""
        def __get__(self):
            return bytes(<char *> (<cpp_instance.ProbSolution *> self._inst).type.c_str()).decode()
    
        def __set__(self, value):
            cdef char * value_proxy
            value_bytes = value.encode()
            (<cpp_instance.ProbSolution *> self._inst).type = std_string(<char *> value_bytes)
    
    
    # methods
    

    pass




def Run(groups, nodes, arcs, solver, verbose=False):
    """Run(groups, nodes, arcs, solver, verbose=False)
    no docstring for Run, please file a bug report!"""
    cdef cpp_vector[cpp_instance.ExGroup] groups_proxy
    cdef int igroups
    cdef int groups_size
    cdef cpp_instance.ExGroup * groups_data
    cdef cpp_vector[cpp_instance.ExNode] nodes_proxy
    cdef int inodes
    cdef int nodes_size
    cdef cpp_instance.ExNode * nodes_data
    cdef cpp_vector[cpp_instance.ExArc] arcs_proxy
    cdef int iarcs
    cdef int arcs_size
    cdef cpp_instance.ExArc * arcs_data
    cdef ExSolver solver_proxy
    cdef cpp_instance.ExSolution rtnval
    # groups is a (('vector', 'ExGroup', 0), '&')
    groups_size = len(groups)
    if isinstance(groups, np.ndarray) and (<np.ndarray> groups).descr.type_num == dtypes.xd_exgroup.num:
        groups_data = <cpp_instance.ExGroup *> np.PyArray_DATA(<np.ndarray> groups)
        groups_proxy = cpp_vector[cpp_instance.ExGroup](<size_t> groups_size)
        for igroups in range(groups_size):
            groups_proxy[igroups] = groups_data[igroups]
    else:
        groups_proxy = cpp_vector[cpp_instance.ExGroup](<size_t> groups_size)
        for igroups in range(groups_size):
            groups_proxy[igroups] = (<cpp_instance.ExGroup *> (<ExGroup> groups[igroups])._inst)[0]
    # nodes is a (('vector', 'ExNode', 0), '&')
    nodes_size = len(nodes)
    if isinstance(nodes, np.ndarray) and (<np.ndarray> nodes).descr.type_num == dtypes.xd_exnode.num:
        nodes_data = <cpp_instance.ExNode *> np.PyArray_DATA(<np.ndarray> nodes)
        nodes_proxy = cpp_vector[cpp_instance.ExNode](<size_t> nodes_size)
        for inodes in range(nodes_size):
            nodes_proxy[inodes] = nodes_data[inodes]
    else:
        nodes_proxy = cpp_vector[cpp_instance.ExNode](<size_t> nodes_size)
        for inodes in range(nodes_size):
            nodes_proxy[inodes] = (<cpp_instance.ExNode *> (<ExNode> nodes[inodes])._inst)[0]
    # arcs is a (('vector', 'ExArc', 0), '&')
    arcs_size = len(arcs)
    if isinstance(arcs, np.ndarray) and (<np.ndarray> arcs).descr.type_num == dtypes.xd_exarc.num:
        arcs_data = <cpp_instance.ExArc *> np.PyArray_DATA(<np.ndarray> arcs)
        arcs_proxy = cpp_vector[cpp_instance.ExArc](<size_t> arcs_size)
        for iarcs in range(arcs_size):
            arcs_proxy[iarcs] = arcs_data[iarcs]
    else:
        arcs_proxy = cpp_vector[cpp_instance.ExArc](<size_t> arcs_size)
        for iarcs in range(arcs_size):
            arcs_proxy[iarcs] = (<cpp_instance.ExArc *> (<ExArc> arcs[iarcs])._inst)[0]
    solver_proxy = <ExSolver> solver
    rtnval = cpp_instance.Run(groups_proxy, nodes_proxy, arcs_proxy, (<cpp_instance.ExSolver *> solver_proxy._inst)[0], <bint> verbose)
    rtnval_proxy = ExSolution()
    (<cpp_instance.ExSolution *> rtnval_proxy._inst)[0] = rtnval
    return rtnval_proxy





cdef class ExNode:
    """no docstring for {'tarbase': 'instance', 'tarname': 'ExNode', 'language': 'c++', 'srcname': 'ExNode', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults


    def _exnode_exnode_0(self, ):
        """ExNode(self, )
        """
        self._inst = new cpp_instance.ExNode()
    
    
    def _exnode_exnode_1(self, id, gid, kind, qty=0, excl=False, excl_id=-1):
        """ExNode(self, id, gid, kind, qty=0, excl=False, excl_id=-1)
        """
        self._inst = new cpp_instance.ExNode(<int> id, <int> gid, <bint> kind, <double> qty, <bint> excl, <int> excl_id)
    
    
    def _exnode_exnode_2(self, other):
        """ExNode(self, other)
        """
        cdef ExNode other_proxy
        other_proxy = <ExNode> other
        self._inst = new cpp_instance.ExNode((<cpp_instance.ExNode *> other_proxy._inst)[0])
    
    
    _exnode_exnode_0_argtypes = frozenset()
    _exnode_exnode_1_argtypes = frozenset(((0, int), (1, int), (2, bool), (3, float), (4, bool), (5, int), ("id", int), ("gid", int), ("kind", bool), ("qty", float), ("excl", bool), ("excl_id", int)))
    _exnode_exnode_2_argtypes = frozenset(((0, ExNode), ("other", ExNode)))
    
    def __init__(self, *args, **kwargs):
        """ExNode(self, other)
        """
        types = set([(i, type(a)) for i, a in enumerate(args)])
        types.update([(k, type(v)) for k, v in kwargs.items()])
        # vtable-like dispatch for exactly matching types
        if types <= self._exnode_exnode_0_argtypes:
            self._exnode_exnode_0(*args, **kwargs)
            return
        if types <= self._exnode_exnode_2_argtypes:
            self._exnode_exnode_2(*args, **kwargs)
            return
        if types <= self._exnode_exnode_1_argtypes:
            self._exnode_exnode_1(*args, **kwargs)
            return
        # duck-typed dispatch based on whatever works!
        try:
            self._exnode_exnode_0(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exnode_exnode_2(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exnode_exnode_1(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        raise RuntimeError('method __init__() could not be dispatched')
    
    def __dealloc__(self):
        if self._free_inst and self._inst is not NULL:
            free(self._inst)

    # attributes
    property excl:
        """no docstring for excl, please file a bug report!"""
        def __get__(self):
            return bool((<cpp_instance.ExNode *> self._inst).excl)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).excl = <bint> value
    
    
    property excl_id:
        """no docstring for excl_id, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExNode *> self._inst).excl_id)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).excl_id = <int> value
    
    
    property gid:
        """no docstring for gid, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExNode *> self._inst).gid)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).gid = <int> value
    
    
    property id:
        """no docstring for id, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExNode *> self._inst).id)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).id = <int> value
    
    
    property kind:
        """no docstring for kind, please file a bug report!"""
        def __get__(self):
            return bool((<cpp_instance.ExNode *> self._inst).kind)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).kind = <bint> value
    
    
    property qty:
        """no docstring for qty, please file a bug report!"""
        def __get__(self):
            return float((<cpp_instance.ExNode *> self._inst).qty)
    
        def __set__(self, value):
            (<cpp_instance.ExNode *> self._inst).qty = <double> value
    
    
    # methods
    

    pass





cdef class ExSolution(ProbSolution):
    """no docstring for {'tarbase': 'instance', 'tarname': 'ExSolution', 'language': 'c++', 'srcname': 'ExSolution', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults
        self._flows = None

    def __init__(self, time=0, objective=0, type='', cyclus_version=''):
        """ExSolution(self, time=0, objective=0, type='', cyclus_version='')
        """
        cdef char * type_proxy
        cdef char * cyclus_version_proxy
        type_bytes = type.encode()
        cyclus_version_bytes = cyclus_version.encode()
        self._inst = new cpp_instance.ExSolution(<double> time, <double> objective, std_string(<char *> type_bytes), std_string(<char *> cyclus_version_bytes))
    
    

    # attributes
    property flows:
        """no docstring for flows, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble flows_proxy
            if self._flows is None:
                flows_proxy = stlcontainers.MapIntDouble(False, False)
                flows_proxy.map_ptr = &(<cpp_instance.ExSolution *> self._inst).flows
                self._flows = flows_proxy
            return self._flows
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_instance.ExSolution *> self._inst).flows = value_proxy.map_ptr[0]
            self._flows = None
    
    
    # methods
    

    pass





cdef class ExGroup:
    """no docstring for {'tarbase': 'instance', 'tarname': 'ExGroup', 'language': 'c++', 'srcname': 'ExGroup', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults
        self._caps = None

    def _exgroup_exgroup_0(self, ):
        """ExGroup(self, )
        """
        self._inst = new cpp_instance.ExGroup()
    
    
    def _exgroup_exgroup_1(self, id, kind, caps, qty=0):
        """ExGroup(self, id, kind, caps, qty=0)
        """
        cdef cpp_vector[double] caps_proxy
        cdef int icaps
        cdef int caps_size
        cdef double * caps_data
        # caps is a (('vector', 'float64', 0), '&')
        caps_size = len(caps)
        if isinstance(caps, np.ndarray) and (<np.ndarray> caps).descr.type_num == np.NPY_FLOAT64:
            caps_data = <double *> np.PyArray_DATA(<np.ndarray> caps)
            caps_proxy = cpp_vector[double](<size_t> caps_size)
            for icaps in range(caps_size):
                caps_proxy[icaps] = caps_data[icaps]
        else:
            caps_proxy = cpp_vector[double](<size_t> caps_size)
            for icaps in range(caps_size):
                caps_proxy[icaps] = <double> caps[icaps]
        self._inst = new cpp_instance.ExGroup(<int> id, <bint> kind, caps_proxy, <double> qty)
    
    
    def _exgroup_exgroup_2(self, other):
        """ExGroup(self, other)
        """
        cdef ExGroup other_proxy
        other_proxy = <ExGroup> other
        self._inst = new cpp_instance.ExGroup((<cpp_instance.ExGroup *> other_proxy._inst)[0])
    
    
    _exgroup_exgroup_0_argtypes = frozenset()
    _exgroup_exgroup_1_argtypes = frozenset(((0, int), (1, bool), (2, np.ndarray), (3, float), ("id", int), ("kind", bool), ("caps", np.ndarray), ("qty", float)))
    _exgroup_exgroup_2_argtypes = frozenset(((0, ExGroup), ("other", ExGroup)))
    
    def __init__(self, *args, **kwargs):
        """ExGroup(self, other)
        """
        types = set([(i, type(a)) for i, a in enumerate(args)])
        types.update([(k, type(v)) for k, v in kwargs.items()])
        # vtable-like dispatch for exactly matching types
        if types <= self._exgroup_exgroup_0_argtypes:
            self._exgroup_exgroup_0(*args, **kwargs)
            return
        if types <= self._exgroup_exgroup_2_argtypes:
            self._exgroup_exgroup_2(*args, **kwargs)
            return
        if types <= self._exgroup_exgroup_1_argtypes:
            self._exgroup_exgroup_1(*args, **kwargs)
            return
        # duck-typed dispatch based on whatever works!
        try:
            self._exgroup_exgroup_0(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exgroup_exgroup_2(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exgroup_exgroup_1(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        raise RuntimeError('method __init__() could not be dispatched')
    
    def __dealloc__(self):
        if self._free_inst and self._inst is not NULL:
            free(self._inst)

    # attributes
    property caps:
        """no docstring for caps, please file a bug report!"""
        def __get__(self):
            cdef np.ndarray caps_proxy
            cdef np.npy_intp caps_proxy_shape[1]
            if self._caps is None:
                caps_proxy_shape[0] = <np.npy_intp> (<cpp_instance.ExGroup *> self._inst).caps.size()
                caps_proxy = np.PyArray_SimpleNewFromData(1, caps_proxy_shape, np.NPY_FLOAT64, &(<cpp_instance.ExGroup *> self._inst).caps[0])
                self._caps = caps_proxy
            return self._caps
    
        def __set__(self, value):
            cdef cpp_vector[double] value_proxy
            cdef int ivalue
            cdef int value_size
            cdef double * value_data
            # value is a ('vector', 'float64', 0)
            value_size = len(value)
            if isinstance(value, np.ndarray) and (<np.ndarray> value).descr.type_num == np.NPY_FLOAT64:
                value_data = <double *> np.PyArray_DATA(<np.ndarray> value)
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = value_data[ivalue]
            else:
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = <double> value[ivalue]
            (<cpp_instance.ExGroup *> self._inst).caps = value_proxy
            self._caps = None
    
    
    property id:
        """no docstring for id, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExGroup *> self._inst).id)
    
        def __set__(self, value):
            (<cpp_instance.ExGroup *> self._inst).id = <int> value
    
    
    property kind:
        """no docstring for kind, please file a bug report!"""
        def __get__(self):
            return bool((<cpp_instance.ExGroup *> self._inst).kind)
    
        def __set__(self, value):
            (<cpp_instance.ExGroup *> self._inst).kind = <bint> value
    
    
    property qty:
        """no docstring for qty, please file a bug report!"""
        def __get__(self):
            return float((<cpp_instance.ExGroup *> self._inst).qty)
    
        def __set__(self, value):
            (<cpp_instance.ExGroup *> self._inst).qty = <double> value
    
    
    # methods
    

    pass






cdef class ExSolver:
    """no docstring for {'tarbase': 'instance', 'tarname': 'ExSolver', 'language': 'c++', 'srcname': 'ExSolver', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults


    def __init__(self, type='cbc'):
        """ExSolver(self, type='cbc')
        """
        cdef char * type_proxy
        type_bytes = type.encode()
        self._inst = new cpp_instance.ExSolver(std_string(<char *> type_bytes))
    
    
    def __dealloc__(self):
        if self._free_inst and self._inst is not NULL:
            free(self._inst)

    # attributes
    property type:
        """no docstring for type, please file a bug report!"""
        def __get__(self):
            return bytes(<char *> (<cpp_instance.ExSolver *> self._inst).type.c_str()).decode()
    
        def __set__(self, value):
            cdef char * value_proxy
            value_bytes = value.encode()
            (<cpp_instance.ExSolver *> self._inst).type = std_string(<char *> value_bytes)
    
    
    # methods
    

    pass





cdef class ExArc:
    """no docstring for {'tarbase': 'instance', 'tarname': 'ExArc', 'language': 'c++', 'srcname': 'ExArc', 'sidecars': (), 'incfiles': ('instance.h',), 'srcfiles': ('cpp/instance.cc', 'cpp/instance.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults
        self._ucaps = None
        self._vcaps = None

    def _exarc_exarc_0(self, ):
        """ExArc(self, )
        """
        self._inst = new cpp_instance.ExArc()
    
    
    def _exarc_exarc_1(self, id, uid, ucaps, vid, vcaps, pref):
        """ExArc(self, id, uid, ucaps, vid, vcaps, pref)
        """
        cdef cpp_vector[double] ucaps_proxy
        cdef int iucaps
        cdef int ucaps_size
        cdef double * ucaps_data
        cdef cpp_vector[double] vcaps_proxy
        cdef int ivcaps
        cdef int vcaps_size
        cdef double * vcaps_data
        # ucaps is a (('vector', 'float64', 0), '&')
        ucaps_size = len(ucaps)
        if isinstance(ucaps, np.ndarray) and (<np.ndarray> ucaps).descr.type_num == np.NPY_FLOAT64:
            ucaps_data = <double *> np.PyArray_DATA(<np.ndarray> ucaps)
            ucaps_proxy = cpp_vector[double](<size_t> ucaps_size)
            for iucaps in range(ucaps_size):
                ucaps_proxy[iucaps] = ucaps_data[iucaps]
        else:
            ucaps_proxy = cpp_vector[double](<size_t> ucaps_size)
            for iucaps in range(ucaps_size):
                ucaps_proxy[iucaps] = <double> ucaps[iucaps]
        # vcaps is a (('vector', 'float64', 0), '&')
        vcaps_size = len(vcaps)
        if isinstance(vcaps, np.ndarray) and (<np.ndarray> vcaps).descr.type_num == np.NPY_FLOAT64:
            vcaps_data = <double *> np.PyArray_DATA(<np.ndarray> vcaps)
            vcaps_proxy = cpp_vector[double](<size_t> vcaps_size)
            for ivcaps in range(vcaps_size):
                vcaps_proxy[ivcaps] = vcaps_data[ivcaps]
        else:
            vcaps_proxy = cpp_vector[double](<size_t> vcaps_size)
            for ivcaps in range(vcaps_size):
                vcaps_proxy[ivcaps] = <double> vcaps[ivcaps]
        self._inst = new cpp_instance.ExArc(<int> id, <int> uid, ucaps_proxy, <int> vid, vcaps_proxy, <double> pref)
    
    
    def _exarc_exarc_2(self, other):
        """ExArc(self, other)
        """
        cdef ExArc other_proxy
        other_proxy = <ExArc> other
        self._inst = new cpp_instance.ExArc((<cpp_instance.ExArc *> other_proxy._inst)[0])
    
    
    _exarc_exarc_0_argtypes = frozenset()
    _exarc_exarc_1_argtypes = frozenset(((0, int), (1, int), (2, np.ndarray), (3, int), (4, np.ndarray), (5, float), ("id", int), ("uid", int), ("ucaps", np.ndarray), ("vid", int), ("vcaps", np.ndarray), ("pref", float)))
    _exarc_exarc_2_argtypes = frozenset(((0, ExArc), ("other", ExArc)))
    
    def __init__(self, *args, **kwargs):
        """ExArc(self, other)
        """
        types = set([(i, type(a)) for i, a in enumerate(args)])
        types.update([(k, type(v)) for k, v in kwargs.items()])
        # vtable-like dispatch for exactly matching types
        if types <= self._exarc_exarc_0_argtypes:
            self._exarc_exarc_0(*args, **kwargs)
            return
        if types <= self._exarc_exarc_2_argtypes:
            self._exarc_exarc_2(*args, **kwargs)
            return
        if types <= self._exarc_exarc_1_argtypes:
            self._exarc_exarc_1(*args, **kwargs)
            return
        # duck-typed dispatch based on whatever works!
        try:
            self._exarc_exarc_0(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exarc_exarc_2(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._exarc_exarc_1(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        raise RuntimeError('method __init__() could not be dispatched')
    
    def __dealloc__(self):
        if self._free_inst and self._inst is not NULL:
            free(self._inst)

    # attributes
    property id:
        """no docstring for id, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExArc *> self._inst).id)
    
        def __set__(self, value):
            (<cpp_instance.ExArc *> self._inst).id = <int> value
    
    
    property pref:
        """no docstring for pref, please file a bug report!"""
        def __get__(self):
            return float((<cpp_instance.ExArc *> self._inst).pref)
    
        def __set__(self, value):
            (<cpp_instance.ExArc *> self._inst).pref = <double> value
    
    
    property ucaps:
        """no docstring for ucaps, please file a bug report!"""
        def __get__(self):
            cdef np.ndarray ucaps_proxy
            cdef np.npy_intp ucaps_proxy_shape[1]
            if self._ucaps is None:
                ucaps_proxy_shape[0] = <np.npy_intp> (<cpp_instance.ExArc *> self._inst).ucaps.size()
                ucaps_proxy = np.PyArray_SimpleNewFromData(1, ucaps_proxy_shape, np.NPY_FLOAT64, &(<cpp_instance.ExArc *> self._inst).ucaps[0])
                self._ucaps = ucaps_proxy
            return self._ucaps
    
        def __set__(self, value):
            cdef cpp_vector[double] value_proxy
            cdef int ivalue
            cdef int value_size
            cdef double * value_data
            # value is a ('vector', 'float64', 0)
            value_size = len(value)
            if isinstance(value, np.ndarray) and (<np.ndarray> value).descr.type_num == np.NPY_FLOAT64:
                value_data = <double *> np.PyArray_DATA(<np.ndarray> value)
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = value_data[ivalue]
            else:
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = <double> value[ivalue]
            (<cpp_instance.ExArc *> self._inst).ucaps = value_proxy
            self._ucaps = None
    
    
    property uid:
        """no docstring for uid, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExArc *> self._inst).uid)
    
        def __set__(self, value):
            (<cpp_instance.ExArc *> self._inst).uid = <int> value
    
    
    property vcaps:
        """no docstring for vcaps, please file a bug report!"""
        def __get__(self):
            cdef np.ndarray vcaps_proxy
            cdef np.npy_intp vcaps_proxy_shape[1]
            if self._vcaps is None:
                vcaps_proxy_shape[0] = <np.npy_intp> (<cpp_instance.ExArc *> self._inst).vcaps.size()
                vcaps_proxy = np.PyArray_SimpleNewFromData(1, vcaps_proxy_shape, np.NPY_FLOAT64, &(<cpp_instance.ExArc *> self._inst).vcaps[0])
                self._vcaps = vcaps_proxy
            return self._vcaps
    
        def __set__(self, value):
            cdef cpp_vector[double] value_proxy
            cdef int ivalue
            cdef int value_size
            cdef double * value_data
            # value is a ('vector', 'float64', 0)
            value_size = len(value)
            if isinstance(value, np.ndarray) and (<np.ndarray> value).descr.type_num == np.NPY_FLOAT64:
                value_data = <double *> np.PyArray_DATA(<np.ndarray> value)
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = value_data[ivalue]
            else:
                value_proxy = cpp_vector[double](<size_t> value_size)
                for ivalue in range(value_size):
                    value_proxy[ivalue] = <double> value[ivalue]
            (<cpp_instance.ExArc *> self._inst).vcaps = value_proxy
            self._vcaps = None
    
    
    property vid:
        """no docstring for vid, please file a bug report!"""
        def __get__(self):
            return int((<cpp_instance.ExArc *> self._inst).vid)
    
        def __set__(self, value):
            (<cpp_instance.ExArc *> self._inst).vid = <int> value
    
    
    # methods
    

    pass






{'cpppxd_footer': '', 'pyx_header': '', 'pxd_header': '', 'pxd_footer': '', 'cpppxd_header': '', 'pyx_footer': ''}
