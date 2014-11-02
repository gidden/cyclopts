"""A module for I/O helper functions, classes, etc."""

from collections import defaultdict

class PathMap(object):
    """A simple container class for mapping columns to Hdf5 paths"""
    
    def __init__(self, col=None):
        """Parameters
        ----------
        col : str
            the column name
        """
        self.col = col
        
    @property
    def path(self):
        """Subclasses must implement this method to provide the path to the
        column name"""
        raise NotImplementedError

def value_mapping(tbl, x, y, uuids=True):
    """Returns a mapping from x to a list of ys in a table. A table can be
    supplied, or the underlying table will be used by default. If uuids is
    true, the cyclopts.tools.str_to_uuid function is used for both x and
    y."""
    ret = defaultdict(list)
    if uuids:
        for row in tbl.iterrows():
            ret[tools.str_to_uuid(row[x])].append(tools.str_to_uuid(row[y]))
    else:
        for row in tbl.iterrows():
            ret[row[x]].append(row[y])
    return ret

def grab_data(h5file, path, col, matching=None):
    """Grabs data in a path matching parameters
    
    Parameters
    ----------
    h5file : PyTables HDF5 File handle
    path : str
        the path to the appropriate table
    col : str
        the target column name
    matching : tuple, optional
        a tuple of col name and data to match, if no match is given, all column
        values will be returned

    Returns
    -------
    data : list, dict, other
        if a matching is provided, a dictionary from the instance id to the
        data value is returned, otherwise a list of all column values is given
    """
    h5node = h5file.get_node(path)
    if matching is None:
        data = [x[col] for x in h5node.iterrows()]
    else:
        data = []
        scol, search = matching
        data = {x['instid']: x[col] for x in h5node.iterrows() if x[scol] in search}
    return data

def param_mapping(h5file, path, kcol, vcol):
    """return a mapping of params to all values found
    
    Parameters
    ----------
    h5file : PyTables HDF5 File handle
    path : str
        the path to the appropriate table
    kcol : str
        the key column name
    vcol : str
        the value column name
    
    Return
    ------
    mapping : dict
        a mapping from key columns to a set of all found value columns
    """
    h5node = h5file.get_node(path)
    data = defaultdict(set)
    for x in h5node.iterrows():
        data[x[kcol]].add(x[vcol])
    return data

def param_to_iids(h5file, fam_path, sp_path, col):
    """Return a mapping of parameter values to instids
    
    Parameters
    ----------
    h5file : PyTables HDF5 File handle
    fam_path : str
        the path to the appropriate family table (for param ids to inst ids)
    sp_path : str
        the path to the appropriate species table (for param to param ids)
    col : str
        the parameter column name

    Return
    ------
    mapping : dict
        a mapping from key columns to a set of all found value columns
    """
    pid_to_iids = param_mapping(h5file, fam_path, 'paramid', 'instid')
    ret = defaultdict(set)
    for p, pids in param_mapping(h5file, sp_path, col, 'paramid').items():
        for pid in pids:
            ret[p].update(pid_to_iids[pid])
    return ret

def tbl_to_dict(tbl, key):
    rows = tbl.read()
    keys = tbl.coltypes.keys()
    keys.remove(key)
    return {x[key]: {k: x[k] for k in keys} for x in rows}
