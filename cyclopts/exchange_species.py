
from cyclopts.problems import ProblemSpecies
from cyclopts.cyclopts_io import Table as cycTable
from cyclopts.exchange_family import ResourceExchange
from cyclopts.params import Param, BoolParam, CoeffParam, SupConstrParam

class RandomRequestPoint(object):
    """A container class representing a point in parameter space for
    RandomRequest problem species.
    """
    def __init__(self, n_commods = None, 
                 n_request = None, assem_per_req = None, req_qty = None, 
                 assem_multi_commod = None, 
                 req_multi_commods = None, exclusive = None, n_req_constr = None, 
                 n_supply = None, sup_multi = None, sup_multi_commods = None, 
                 n_sup_constr = None, sup_constr_val = None, 
                 connection = None, constr_coeff = None, pref_coeff = None):
        """Parameters
        ----------
        n_commods : Param or similar, optional
            the number of commodities
        n_request : Param or similar, optional
            the number of requesters (i.e., RequestGroups)
        assem_per_req : Param or similar, optional
            the number of assemblies in a request
        req_qty : Param or similar, optional
            the quantity associated with each request
        assem_multi_commod : BoolParam or similar, optional
            whether an assembly request can be satisfied by multiple 
            commodities
        req_multi_commods : Param or similar, optional
            the number of commodities in a multicommodity zone
        exclusive : BoolParam or similar, optional
            the probability that a reactor assembly request is exclusive
        n_req_constr : Param or similar, optional
            the number of constraints associated with a given request group
        n_supply : Param or similar, optional
            the number of suppliers (i.e., supply ExchangeNodeGroups)
        sup_multi : BoolParam or similar, optional
            whether a supplier supplies more than one commodity
        sup_multi_commods : Param or similar, optional
            the number of commodities a multicommodity supplier supplies
        n_sup_constr : Param or similar, optional
            the number of constraints associated with a given supply group
        sup_constr_val : SupConstrParam or similar, optional
            the supply constraint rhs value (as a fraction of the total request 
            amount for a commodity)
        connection : BoolParam or similar, optional
            the probability that a possible connection between supply and 
            request nodes is added
        constr_coeff : CoeffParam or similar, optional
            constraint coefficients
        pref_coeff : CoeffParam or similar, optional
            preference coefficients
        """
        self.paramid = uuid.uuid4()
        self.n_commods = n_commods \
            if n_commods is not None else Param(1)
        self.n_request = n_request \
            if n_request is not None else Param(1)
        self.assem_per_req = assem_per_req \
            if assem_per_req is not None else Param(1)
        self.req_qty = req_qty \
            if req_qty is not None else Param(1)
        self.assem_multi_commod = assem_multi_commod \
            if assem_multi_commod is not None else BoolParam(-1.0) # never true
        self.req_multi_commods = req_multi_commods \
            if req_multi_commods is not None else Param(0)
        self.exclusive = exclusive \
            if exclusive is not None else BoolParam(-1.0) # never true
        self.n_req_constr = n_req_constr \
            if n_req_constr is not None else Param(0)
        self.n_supply = n_supply \
            if n_supply is not None else Param(1)
        self.sup_multi = sup_multi \
            if sup_multi is not None else BoolParam(-1.0) # never true
        self.sup_multi_commods = sup_multi_commods \
            if sup_multi_commods is not None else Param(0)
        self.n_sup_constr = n_sup_constr \
            if n_sup_constr is not None else Param(1)
        self.sup_constr_val = sup_constr_val \
            if sup_constr_val is not None else SupConstrParam(1.0)
        self.connection = connection \
            if connection is not None else BoolParam(1.0)
        self.constr_coeff = constr_coeff \
            if constr_coeff is not None else CoeffParam(1e-10, 2.0)
        # 1e-10 is 'sufficiently' low
        self.pref_coeff = pref_coeff \
            if pref_coeff is not None else CoeffParam(1e-10, 1.0) 

    def __eq__(self, other):
        for k, exp in self.__dict__.items():
            if k not in other.__dict__:
                return False
            if k == 'paramid':
                continue
            # this is a hack because for some reason for CoeffParams, a == b is
            # true and a != b is true, but I can't get corresponding behavior in
            # ipython. weird.
            if not exp == other.__dict__[k]:
                return False
        return True

    def __str__(self):
        ret = ["{0} = {1}".format(k, getattr(self, k).__str__()) \
                   for k, v in self.__dict__.items()]
        return "ReactorRequestSampler\n{0}".format("\n".join(ret))

    def _dt_convert(self, obj):
        """Converts a python object to its numpy dtype. Nones are converted to
        strings, and all strings are set to size == 32.
        """
        if obj == None or isinstance(obj, basestring):
            return np.dtype('|S32')
        if isinstance(obj, collections.Sequence):
            return np.dtype('|S32')
        else:
            return np.dtype(type(obj))

    def _convert_seq(self, val):
        """converts a string representation of a sequence into a list"""
        return [float(i) for i in \
                    re.sub('[\]\[,]', '', str(val)).split()]

    def describe_h5(self):
        """Returns a numpy dtype describing all composed objects."""
        # np.dtype([("{0}_{1}".format(name, subname), self._dt_convert(subobj)) \
        #               for subname, subobj in obj.__dict__.items() \
        #               for name, obj in self.__dict__.items()])
        ret = []
        for name, obj in self.__dict__.items():
            if name == 'paramid':
                ret.append((name, ('str', 16)))
                continue
            for subname, subobj in obj.__dict__.items():
                if subname.startswith('_'):
                    continue
                ret.append(("{0}_{1}".format(name, subname), 
                            self._dt_convert(subobj)))
        return np.dtype(ret)

    def _is_seq_not_str(self, attr):
        return isinstance(attr, collections.Sequence) \
            and not isinstance(attr, basestring)
    
    def import_h5(self, row):
        for name, obj in self.__dict__.items():
            if name == 'paramid':
                setattr(obj, name, UUID.uuid(bytes=row[name]))
                continue
            for subname, subobj in obj.__dict__.items():
                if subname.startswith('_'):
                    continue
                attr = getattr(obj, subname)
                val = row["{0}_{1}".format(name, subname)]
                if val == 'None':
                    val = None
                elif self._is_seq_not_str(attr):
                    val = self._convert_seq(val)
                setattr(obj, subname, val)
            obj.init()
                
    def export_h5(self, row):
        for name, obj in self.__dict__.items():
            if name == 'paramid':
                row[name] = obj.bytes
                continue
            for subname, subobj in obj.__dict__.items():
                if subname.startswith('_'):
                    continue
                attr = getattr(obj, subname)
                row["{0}_{1}".format(name, subname)] = \
                    str(attr) if self._is_seq_not_str(attr) else attr

    def valid(self):
        """Provides a best-guess estimate as to whether or not a given data
        point, as represented by this Sampler, is valid in the domain-defined
        parameter space.

        Returns
        -------
        bool
            whether the sampler's parameters form a valid point in the 
            sampler's parameter space
        """
        conditions = []
        # there must be at least as many suppliers as commodities
        conditions.append(self.n_commods.avg <= self.n_supply.avg)
        # there must be at least as many requesters as commodities
        conditions.append(self.n_commods.avg <= \
                              (1 + self.req_multi_commods.avg) * self.n_request.avg)
        # there must be at least as many commodities as possible commodities
        # requestable
        conditions.append(self.n_commods.avg > self.req_multi_commods.avg)
        
        # there must be at least as many commodities as possible commodities
        # suppliable
        conditions.append(self.n_commods.avg > self.sup_multi_commods.avg)
        return all(c for c in conditions)
    

class RandomRequest(ProblemSpecies):
    """@TODO"""

    def __init__(self):
        super(RandomRequest, self).__init__()

    @property
    def family(self):
        """Returns
        -------
        family : ResourceExchange
            An instance of this species' family
        """
        return ResourceExchange()

    @property
    def name(self):
        """Returns
        -------
        name : string
            The name of this species
        """
        return 'RandomRequest'

    def register_tables(self, h5file, prefix):
        """Derived classes must implement this function and return their list of
        tables
        
        Parameters
        ----------
        h5file : PyTables File
            the hdf5 file
        prefix : string
            the absolute path to the group for tables of this species

        Returns
        -------
        tables : list of cyclopts_io.Tables
            All tables that could be written to by this species.
        """
        pass

    def read_space(self, space_dict):
        """Derived classes must implement this function.

        Parameters
        ----------
        space_dict : dict
            A dictionary container resulting from the reading in of a run 
            control file
        """
        pass

    @property
    def n_points(self):
        """Derived classes must implement this function returning the number of
        points in its parameter space.
        
        Returns
        -------
        n : int
            The total number of points in the parameter space
        """
        pass
    
    def next_point(self):
        """Derived classes must implement this function returning a
        representation of a point in its parameter space to be used by other
        class member functions.
        
        Returns
        -------
        point : tuple or other
            A representation of a point in parameter space to be used by this 
            species
        """
        pass    

    def record_point(self, point, tables):
        """Derived classes must implement this function, recording information
        about a parameter point in the appropriate tables.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
        tables : list of cyclopts_io.Table
            The tables that can be written to
        """
        pass

    def gen_instance(self, point):
        """Derived classes must implement this function, returning a
        representation of a problem instance.
        
        Parameters
        ----------
        point : tuple or other
            A representation of a point in parameter space
           
        Returns
        -------
        inst : tuple or other
            A representation of a problem instance to be used by this species' 
            family
        """
        pass
