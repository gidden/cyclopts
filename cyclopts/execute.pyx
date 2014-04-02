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
from libc.stdlib cimport malloc
from libcpp cimport bool as cpp_bool
from libcpp.map cimport map as cpp_map
from libcpp.string cimport string as std_string
from libcpp.vector cimport vector as cpp_vector

import collections
import numpy as np
import stlcontainers

np.import_array()



cdef class RequestParams:
    """no docstring for {'tarbase': 'execute', 'tarname': 'RequestParams', 'language': 'c++', 'srcname': 'RequestParams', 'sidecars': (), 'incfiles': ('execute.h',), 'srcfiles': ('cpp/execute.cc', 'cpp/execute.h')}, please file a bug report!"""



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
        self._def_constr_val = None
        self._node_ucaps = None
        self._req_qty = None
        self._u_node_excl = None
        self._u_node_qty = None
        self._u_nodes_per_req = None

    def __init__(self, ):
        """RequestParams(self, )
        """
        self._inst = malloc(sizeof(cpp_execute.RequestParams))
        (<cpp_execute.RequestParams *> self._inst)[0] = cpp_execute.RequestParams()
    
    
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
                arc_pref_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).arc_pref
                self._arc_pref = arc_pref_proxy
            return self._arc_pref
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.RequestParams *> self._inst).arc_pref = value_proxy.map_ptr[0]
            self._arc_pref = None
    
    
    property arc_to_unode:
        """no docstring for arc_to_unode, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntInt arc_to_unode_proxy
            if self._arc_to_unode is None:
                arc_to_unode_proxy = stlcontainers.MapIntInt(False, False)
                arc_to_unode_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).arc_to_unode
                self._arc_to_unode = arc_to_unode_proxy
            return self._arc_to_unode
    
        def __set__(self, value):
            cdef stlcontainers._MapIntInt value_proxy
            value_proxy = stlcontainers.MapIntInt(value, not isinstance(value, stlcontainers._MapIntInt))
            (<cpp_execute.RequestParams *> self._inst).arc_to_unode = value_proxy.map_ptr[0]
            self._arc_to_unode = None
    
    
    property arc_to_vnode:
        """no docstring for arc_to_vnode, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntInt arc_to_vnode_proxy
            if self._arc_to_vnode is None:
                arc_to_vnode_proxy = stlcontainers.MapIntInt(False, False)
                arc_to_vnode_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).arc_to_vnode
                self._arc_to_vnode = arc_to_vnode_proxy
            return self._arc_to_vnode
    
        def __set__(self, value):
            cdef stlcontainers._MapIntInt value_proxy
            value_proxy = stlcontainers.MapIntInt(value, not isinstance(value, stlcontainers._MapIntInt))
            (<cpp_execute.RequestParams *> self._inst).arc_to_vnode = value_proxy.map_ptr[0]
            self._arc_to_vnode = None
    
    
    property constr_vals:
        """no docstring for constr_vals, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorDouble constr_vals_proxy
            if self._constr_vals is None:
                constr_vals_proxy = stlcontainers.MapIntVectorDouble(False, False)
                constr_vals_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).constr_vals
                self._constr_vals = constr_vals_proxy
            return self._constr_vals
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorDouble value_proxy
            value_proxy = stlcontainers.MapIntVectorDouble(value, not isinstance(value, stlcontainers._MapIntVectorDouble))
            (<cpp_execute.RequestParams *> self._inst).constr_vals = value_proxy.map_ptr[0]
            self._constr_vals = None
    
    
    property def_constr_coeffs:
        """no docstring for def_constr_coeffs, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble def_constr_coeffs_proxy
            if self._def_constr_coeffs is None:
                def_constr_coeffs_proxy = stlcontainers.MapIntDouble(False, False)
                def_constr_coeffs_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).def_constr_coeffs
                self._def_constr_coeffs = def_constr_coeffs_proxy
            return self._def_constr_coeffs
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.RequestParams *> self._inst).def_constr_coeffs = value_proxy.map_ptr[0]
            self._def_constr_coeffs = None
    
    
    property def_constr_val:
        """no docstring for def_constr_val, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble def_constr_val_proxy
            if self._def_constr_val is None:
                def_constr_val_proxy = stlcontainers.MapIntDouble(False, False)
                def_constr_val_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).def_constr_val
                self._def_constr_val = def_constr_val_proxy
            return self._def_constr_val
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.RequestParams *> self._inst).def_constr_val = value_proxy.map_ptr[0]
            self._def_constr_val = None
    
    
    property node_ucaps:
        """no docstring for node_ucaps, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntMapIntVectorDouble node_ucaps_proxy
            if self._node_ucaps is None:
                node_ucaps_proxy = stlcontainers.MapIntMapIntVectorDouble(False, False)
                node_ucaps_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).node_ucaps
                self._node_ucaps = node_ucaps_proxy
            return self._node_ucaps
    
        def __set__(self, value):
            cdef stlcontainers._MapIntMapIntVectorDouble value_proxy
            value_proxy = stlcontainers.MapIntMapIntVectorDouble(value, not isinstance(value, stlcontainers._MapIntMapIntVectorDouble))
            (<cpp_execute.RequestParams *> self._inst).node_ucaps = value_proxy.map_ptr[0]
            self._node_ucaps = None
    
    
    property req_qty:
        """no docstring for req_qty, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble req_qty_proxy
            if self._req_qty is None:
                req_qty_proxy = stlcontainers.MapIntDouble(False, False)
                req_qty_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).req_qty
                self._req_qty = req_qty_proxy
            return self._req_qty
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.RequestParams *> self._inst).req_qty = value_proxy.map_ptr[0]
            self._req_qty = None
    
    
    property u_node_excl:
        """no docstring for u_node_excl, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntBool u_node_excl_proxy
            if self._u_node_excl is None:
                u_node_excl_proxy = stlcontainers.MapIntBool(False, False)
                u_node_excl_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).u_node_excl
                self._u_node_excl = u_node_excl_proxy
            return self._u_node_excl
    
        def __set__(self, value):
            cdef stlcontainers._MapIntBool value_proxy
            value_proxy = stlcontainers.MapIntBool(value, not isinstance(value, stlcontainers._MapIntBool))
            (<cpp_execute.RequestParams *> self._inst).u_node_excl = value_proxy.map_ptr[0]
            self._u_node_excl = None
    
    
    property u_node_qty:
        """no docstring for u_node_qty, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble u_node_qty_proxy
            if self._u_node_qty is None:
                u_node_qty_proxy = stlcontainers.MapIntDouble(False, False)
                u_node_qty_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).u_node_qty
                self._u_node_qty = u_node_qty_proxy
            return self._u_node_qty
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.RequestParams *> self._inst).u_node_qty = value_proxy.map_ptr[0]
            self._u_node_qty = None
    
    
    property u_nodes_per_req:
        """no docstring for u_nodes_per_req, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntVectorInt u_nodes_per_req_proxy
            if self._u_nodes_per_req is None:
                u_nodes_per_req_proxy = stlcontainers.MapIntVectorInt(False, False)
                u_nodes_per_req_proxy.map_ptr = &(<cpp_execute.RequestParams *> self._inst).u_nodes_per_req
                self._u_nodes_per_req = u_nodes_per_req_proxy
            return self._u_nodes_per_req
    
        def __set__(self, value):
            cdef stlcontainers._MapIntVectorInt value_proxy
            value_proxy = stlcontainers.MapIntVectorInt(value, not isinstance(value, stlcontainers._MapIntVectorInt))
            (<cpp_execute.RequestParams *> self._inst).u_nodes_per_req = value_proxy.map_ptr[0]
            self._u_nodes_per_req = None
    
    
    # methods
    

    pass



def _execute_exchange_0(params, db_path):
    """execute_exchange(params, db_path)
    no docstring for execute_exchange, please file a bug report!"""
    cdef RequestParams params_proxy
    cdef char * db_path_proxy
    params_proxy = <RequestParams> params
    db_path_bytes = db_path.encode()
    cpp_execute.execute_exchange((<cpp_execute.RequestParams *> params_proxy._inst)[0], std_string(<char *> db_path_bytes))


def _execute_exchange_1(params, db_path):
    """execute_exchange(params, db_path)
    no docstring for execute_exchange, please file a bug report!"""
    cdef SupplyParams params_proxy
    cdef char * db_path_proxy
    params_proxy = <SupplyParams> params
    db_path_bytes = db_path.encode()
    cpp_execute.execute_exchange((<cpp_execute.SupplyParams *> params_proxy._inst)[0], std_string(<char *> db_path_bytes))


_execute_exchange_0_argtypes = frozenset(((0, RequestParams), (1, str), ("params", RequestParams), ("db_path", str)))
_execute_exchange_1_argtypes = frozenset(((0, SupplyParams), (1, str), ("params", SupplyParams), ("db_path", str)))

def execute_exchange(*args, **kwargs):
    """execute_exchange(params, db_path)
    no docstring for execute_exchange, please file a bug report!"""
    types = set([(i, type(a)) for i, a in enumerate(args)])
    types.update([(k, type(v)) for k, v in kwargs.items()])
    # vtable-like dispatch for exactly matching types
    if types <= _execute_exchange_0_argtypes:
        return _execute_exchange_0(*args, **kwargs)
    if types <= _execute_exchange_1_argtypes:
        return _execute_exchange_1(*args, **kwargs)
    # duck-typed dispatch based on whatever works!
    try:
        return _execute_exchange_0(*args, **kwargs)
    except (RuntimeError, TypeError, NameError):
        pass
    try:
        return _execute_exchange_1(*args, **kwargs)
    except (RuntimeError, TypeError, NameError):
        pass
    raise RuntimeError('method execute_exchange() could not be dispatched')


def test():
    """test()
    no docstring for test, please file a bug report!"""
    cpp_execute.test()





cdef class SupplyParams:
    """no docstring for {'tarbase': 'execute', 'tarname': 'SupplyParams', 'language': 'c++', 'srcname': 'SupplyParams', 'sidecars': (), 'incfiles': ('execute.h',), 'srcfiles': ('cpp/execute.cc', 'cpp/execute.h')}, please file a bug report!"""



    # constuctors
    def __cinit__(self, *args, **kwargs):
        self._inst = NULL
        self._free_inst = True

        # cached property defaults
        self._node_qtys = None

    def __init__(self, ):
        """SupplyParams(self, )
        """
        self._inst = malloc(sizeof(cpp_execute.SupplyParams))
        (<cpp_execute.SupplyParams *> self._inst)[0] = cpp_execute.SupplyParams()
    
    
    def __dealloc__(self):
        if self._free_inst:
            free(self._inst)

    # attributes
    property node_qtys:
        """no docstring for node_qtys, please file a bug report!"""
        def __get__(self):
            cdef stlcontainers._MapIntDouble node_qtys_proxy
            if self._node_qtys is None:
                node_qtys_proxy = stlcontainers.MapIntDouble(False, False)
                node_qtys_proxy.map_ptr = &(<cpp_execute.SupplyParams *> self._inst).node_qtys
                self._node_qtys = node_qtys_proxy
            return self._node_qtys
    
        def __set__(self, value):
            cdef stlcontainers._MapIntDouble value_proxy
            value_proxy = stlcontainers.MapIntDouble(value, not isinstance(value, stlcontainers._MapIntDouble))
            (<cpp_execute.SupplyParams *> self._inst).node_qtys = value_proxy.map_ptr[0]
            self._node_qtys = None
    
    
    # methods
    

    pass






{'cpppxd_footer': '', 'pyx_header': '', 'pxd_header': '', 'pxd_footer': '', 'cpppxd_header': '', 'pyx_footer': ''}
