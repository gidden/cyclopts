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
cimport cpp_execute
cimport dtypes
cimport execute
cimport numpy as np
cimport stlcontainers
from cyclopts cimport cpp_execute
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



cdef class Params:
    """no docstring for {'sidecars': (), 'tarbase': 'execute', 'tarname': 'Params', 'language': 'c++', 'srcname': 'Params', 'incfiles': ('execute.h',), 'srcfiles': ('cpp/execute.cc', 'cpp/execute.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults
        self._arc_pref = None
        self._arc_to_unode = None
        self._arc_to_vnode = None
        self._constr_vals = None
        self._def_constr_coeffs = None
        self._excl_req_nodes = None
        self._excl_sup_nodes = None
        self._node_excl = None
        self._node_qty = None
        self._node_ucaps = None
        self._req_qty = None
        self._u_nodes_per_req = None
        self._v_nodes_per_sup = None

    def __init__(self, ):
        """Params(self, )
        """
        self._inst = new cpp_execute.Params()
    
    
    def __dealloc__(self):
        if self._free_inst:
            free(self._inst)

    # attributes
    property arc_pref:
        """no docstring for arc_pref, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble arc_pref_proxy
            if self._arc_pref is None:
                arc_pref_proxy = stlcontainers.MapIntDouble(False, False)
                arc_pref_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).arc_pref
                self._arc_pref = arc_pref_proxy
            return self._arc_pref
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.Params *> self._inst).arc_pref = value_proxy.map_ptr[0]
            self._arc_pref = None
    
    
    property arc_to_unode:
        """no docstring for arc_to_unode, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntInt arc_to_unode_proxy
            if self._arc_to_unode is None:
                arc_to_unode_proxy = stlcontainers.MapIntInt(False, False)
                arc_to_unode_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).arc_to_unode
                self._arc_to_unode = arc_to_unode_proxy
            return self._arc_to_unode
    
        def __set__(self, value):
            cdef stlcontainers._MapIntInt value_proxy
            value_proxy = stlcontainers.MapIntInt(value, not isinstance(value, stlcontainers._MapIntInt))
            (<cpp_execute.Params *> self._inst).arc_to_unode = value_proxy.map_ptr[0]
            self._arc_to_unode = None
    
    
    property arc_to_vnode:
        """no docstring for arc_to_vnode, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntInt arc_to_vnode_proxy
            if self._arc_to_vnode is None:
                arc_to_vnode_proxy = stlcontainers.MapIntInt(False, False)
                arc_to_vnode_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).arc_to_vnode
                self._arc_to_vnode = arc_to_vnode_proxy
            return self._arc_to_vnode
    
        def __set__(self, value):
            cdef stlcontainers._MapIntInt value_proxy
            value_proxy = stlcontainers.MapIntInt(value, not isinstance(value, stlcontainers._MapIntInt))
            (<cpp_execute.Params *> self._inst).arc_to_vnode = value_proxy.map_ptr[0]
            self._arc_to_vnode = None
    
    
    property constr_vals:
        """no docstring for constr_vals, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorDouble constr_vals_proxy
            if self._constr_vals is None:
                constr_vals_proxy = stlcontainers.MapIntVectorDouble(False, False)
                constr_vals_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).constr_vals
                self._constr_vals = constr_vals_proxy
            return self._constr_vals
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorDouble value_proxy
            value_proxy = stlcontainers.MapIntVectorDouble(value, not isinstance(value, stlcontainers._MapIntVectorDouble))
            (<cpp_execute.Params *> self._inst).constr_vals = value_proxy.map_ptr[0]
            self._constr_vals = None
    
    
    property def_constr_coeffs:
        """no docstring for def_constr_coeffs, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble def_constr_coeffs_proxy
            if self._def_constr_coeffs is None:
                def_constr_coeffs_proxy = stlcontainers.MapIntDouble(False, False)
                def_constr_coeffs_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).def_constr_coeffs
                self._def_constr_coeffs = def_constr_coeffs_proxy
            return self._def_constr_coeffs
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.Params *> self._inst).def_constr_coeffs = value_proxy.map_ptr[0]
            self._def_constr_coeffs = None
    
    
    property excl_req_nodes:
        """no docstring for excl_req_nodes, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorVectorInt excl_req_nodes_proxy
            if self._excl_req_nodes is None:
                excl_req_nodes_proxy = stlcontainers.MapIntVectorVectorInt(False, False)
                excl_req_nodes_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).excl_req_nodes
                self._excl_req_nodes = excl_req_nodes_proxy
            return self._excl_req_nodes
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorVectorInt value_proxy
            value_proxy = stlcontainers.MapIntVectorVectorInt(value, not isinstance(value, stlcontainers._MapIntVectorVectorInt))
            (<cpp_execute.Params *> self._inst).excl_req_nodes = value_proxy.map_ptr[0]
            self._excl_req_nodes = None
    
    
    property excl_sup_nodes:
        """no docstring for excl_sup_nodes, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorInt excl_sup_nodes_proxy
            if self._excl_sup_nodes is None:
                excl_sup_nodes_proxy = stlcontainers.MapIntVectorInt(False, False)
                excl_sup_nodes_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).excl_sup_nodes
                self._excl_sup_nodes = excl_sup_nodes_proxy
            return self._excl_sup_nodes
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorInt value_proxy
            value_proxy = stlcontainers.MapIntVectorInt(value, not isinstance(value, stlcontainers._MapIntVectorInt))
            (<cpp_execute.Params *> self._inst).excl_sup_nodes = value_proxy.map_ptr[0]
            self._excl_sup_nodes = None
    
    
    property node_excl:
        """no docstring for node_excl, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntBool node_excl_proxy
            if self._node_excl is None:
                node_excl_proxy = stlcontainers.MapIntBool(False, False)
                node_excl_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).node_excl
                self._node_excl = node_excl_proxy
            return self._node_excl
    
        def __set__(self, value):
            cdef stlcontainers._MapIntBool value_proxy
            value_proxy = stlcontainers.MapIntBool(value, not isinstance(value, stlcontainers._MapIntBool))
            (<cpp_execute.Params *> self._inst).node_excl = value_proxy.map_ptr[0]
            self._node_excl = None
    
    
    property node_qty:
        """no docstring for node_qty, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble node_qty_proxy
            if self._node_qty is None:
                node_qty_proxy = stlcontainers.MapIntDouble(False, False)
                node_qty_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).node_qty
                self._node_qty = node_qty_proxy
            return self._node_qty
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.Params *> self._inst).node_qty = value_proxy.map_ptr[0]
            self._node_qty = None
    
    
    property node_ucaps:
        """no docstring for node_ucaps, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntMapIntVectorDouble node_ucaps_proxy
            if self._node_ucaps is None:
                node_ucaps_proxy = stlcontainers.MapIntMapIntVectorDouble(False, False)
                node_ucaps_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).node_ucaps
                self._node_ucaps = node_ucaps_proxy
            return self._node_ucaps
    
        def __set__(self, value):
            cdef stlcontainers._MapIntMapIntVectorDouble value_proxy
            value_proxy = stlcontainers.MapIntMapIntVectorDouble(value, not isinstance(value, stlcontainers._MapIntMapIntVectorDouble))
            (<cpp_execute.Params *> self._inst).node_ucaps = value_proxy.map_ptr[0]
            self._node_ucaps = None
    
    
    property req_qty:
        """no docstring for req_qty, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble req_qty_proxy
            if self._req_qty is None:
                req_qty_proxy = stlcontainers.MapIntDouble(False, False)
                req_qty_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).req_qty
                self._req_qty = req_qty_proxy
            return self._req_qty
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.Params *> self._inst).req_qty = value_proxy.map_ptr[0]
            self._req_qty = None
    
    
    property u_nodes_per_req:
        """no docstring for u_nodes_per_req, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorInt u_nodes_per_req_proxy
            if self._u_nodes_per_req is None:
                u_nodes_per_req_proxy = stlcontainers.MapIntVectorInt(False, False)
                u_nodes_per_req_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).u_nodes_per_req
                self._u_nodes_per_req = u_nodes_per_req_proxy
            return self._u_nodes_per_req
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorInt value_proxy
            value_proxy = stlcontainers.MapIntVectorInt(value, not isinstance(value, stlcontainers._MapIntVectorInt))
            (<cpp_execute.Params *> self._inst).u_nodes_per_req = value_proxy.map_ptr[0]
            self._u_nodes_per_req = None
    
    
    property v_nodes_per_sup:
        """no docstring for v_nodes_per_sup, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorInt v_nodes_per_sup_proxy
            if self._v_nodes_per_sup is None:
                v_nodes_per_sup_proxy = stlcontainers.MapIntVectorInt(False, False)
                v_nodes_per_sup_proxy.map_ptr = &(<cpp_execute.Params *> self._inst).v_nodes_per_sup
                self._v_nodes_per_sup = v_nodes_per_sup_proxy
            return self._v_nodes_per_sup
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorInt value_proxy
            value_proxy = stlcontainers.MapIntVectorInt(value, not isinstance(value, stlcontainers._MapIntVectorInt))
            (<cpp_execute.Params *> self._inst).v_nodes_per_sup = value_proxy.map_ptr[0]
            self._v_nodes_per_sup = None
    
    
    # methods
    

    pass



def test():
    """test()
    no docstring for test, please file a bug report!"""
    cpp_execute.test()



def execute_exchange(params, db_path=''):
    """execute_exchange(params, db_path='')
    no docstring for execute_exchange, please file a bug report!"""
    cdef Params params_proxy
    cdef char * db_path_proxy
    cdef cpp_vector[cpp_execute.ArcFlow] rtnval
    
    cdef np.npy_intp rtnval_proxy_shape[1]
    params_proxy = <Params> params
    db_path_bytes = db_path.encode()
    rtnval = cpp_execute.execute_exchange((<cpp_execute.Params *> params_proxy._inst)[0], std_string(<char *> db_path_bytes))
    rtnval_proxy_shape[0] = <np.npy_intp> rtnval.size()
    rtnval_proxy = np.PyArray_SimpleNewFromData(1, rtnval_proxy_shape, dtypes.xd_arcflow.num, &rtnval[0])
    rtnval_proxy = np.PyArray_Copy(rtnval_proxy)
    return rtnval_proxy





cdef class ArcFlow:
    """no docstring for {'sidecars': (), 'tarbase': 'execute', 'tarname': 'ArcFlow', 'language': 'c++', 'srcname': 'ArcFlow', 'incfiles': ('execute.h',), 'srcfiles': ('cpp/execute.cc', 'cpp/execute.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults


    def _arcflow_arcflow_0(self, ):
        """ArcFlow(self, )
        """
        self._inst = new cpp_execute.ArcFlow()
    
    
    def _arcflow_arcflow_1(self, id, flow):
        """ArcFlow(self, id, flow)
        """
        self._inst = new cpp_execute.ArcFlow(<int> id, <double> flow)
    
    
    def _arcflow_arcflow_2(self, other):
        """ArcFlow(self, other)
        """
        cdef ArcFlow other_proxy
        other_proxy = <ArcFlow> other
        self._inst = new cpp_execute.ArcFlow((<cpp_execute.ArcFlow *> other_proxy._inst)[0])
    
    
    _arcflow_arcflow_0_argtypes = frozenset()
    _arcflow_arcflow_1_argtypes = frozenset(((0, int), (1, float), ("id", int), ("flow", float)))
    _arcflow_arcflow_2_argtypes = frozenset(((0, ArcFlow), ("other", ArcFlow)))
    
    def __init__(self, *args, **kwargs):
        """ArcFlow(self, other)
        """
        types = set([(i, type(a)) for i, a in enumerate(args)])
        types.update([(k, type(v)) for k, v in kwargs.items()])
        # vtable-like dispatch for exactly matching types
        if types <= self._arcflow_arcflow_0_argtypes:
            self._arcflow_arcflow_0(*args, **kwargs)
            return
        if types <= self._arcflow_arcflow_2_argtypes:
            self._arcflow_arcflow_2(*args, **kwargs)
            return
        if types <= self._arcflow_arcflow_1_argtypes:
            self._arcflow_arcflow_1(*args, **kwargs)
            return
        # duck-typed dispatch based on whatever works!
        try:
            self._arcflow_arcflow_0(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._arcflow_arcflow_2(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        try:
            self._arcflow_arcflow_1(*args, **kwargs)
            return
        except (RuntimeError, TypeError, NameError):
            pass
        raise RuntimeError('method __init__() could not be dispatched')
    
    def __dealloc__(self):
        if self._free_inst:
            free(self._inst)

    # attributes
    property flow:
        """no docstring for flow, please file a bug report!"""
        def __get__(self):
            return float((<cpp_execute.ArcFlow *> self._inst).flow)
    
        def __set__(self, value):
            (<cpp_execute.ArcFlow *> self._inst).flow = <double> value
    
    
    property id:
        """no docstring for id, please file a bug report!"""
        def __get__(self):
            return int((<cpp_execute.ArcFlow *> self._inst).id)
    
        def __set__(self, value):
            (<cpp_execute.ArcFlow *> self._inst).id = <int> value
    
    
    # methods
    

    pass






{'cpppxd_footer': '', 'pyx_header': '', 'pxd_header': '', 'pxd_footer': '', 'cpppxd_header': '', 'pyx_footer': ''}
