
import tables as t

def rms_diff(fname, p1, p2, col='flow'):
    """Take the root-mean-square of the difference of values in two tables.

    Parameters
    ----------
    fname : str
        the hdf5 file name
    p1 : str
        the path to the first table
    p2 : str
        the path to the second table
    col : str, optional
        the column name to operate on, defaults to 'flow'
    """
    with t.open_file(fname, mode='r') as f:
        ret = rms(f.get_node(p1)[col] - f.get_node(p2)[col])
    return ret
