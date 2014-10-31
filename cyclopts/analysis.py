import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as lines
from matplotlib.colors import colorConverter
import sys
from collections import defaultdict
from pylab import asarray

def imarkers():
    return iter(['x', 's', 'o', 'v', '^', '+'])

def icolors():
    return iter(['g', 'b', 'r', 'm', 'c', 'y'])

def ipastels():
    for color in icolors():
        yield pastel(color)

#taken from pyplot_examples.py
def pastel(color, weight=1.75):
    """Color to pastel"""
    rgb = asarray(colorConverter.to_rgb(color))
    # scale color
    maxc = max(rgb)
    if maxc < 1.0 and maxc > 0:
        # scale color
        scale = 1.0 / maxc
        rgb = rgb * scale
    # now decrease saturation
    total = sum(rgb)
    slack = 0
    for x in rgb:
        slack += 1.0 - x

    # want to increase weight from total to weight
    # pick x s.t.  slack * x == weight - total
    # x = (weight - total) / slack
    x = (weight - total) / slack

    rgb = [c + (x * (1.0-c)) for c in rgb]

    return rgb

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

def tbl_to_dict(tbl, key):
    rows = tbl.read()
    keys = tbl.coltypes.keys()
    keys.remove(key)
    return {x[key]: {x[k] for k in keys} for x in rows}

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

def multi_scatter(x, ys, colors=None, ax=None):
    """returns a plot object with multiple y values
    
    Parameters
    ----------
    x : array-like of tuples of instids and values
        x values
    ys : dict
        dictionary of labels to instid, tuple y values
    colors : array-like, optional
        array of colors to use
    ax : pyplot.axis, optional
        an axis on which to plot
    
    Return
    ------
    ax : pyplot.axis
        the plotted axis
    """
    c_it = icolors() if colors is None else iter(colors)
    if ax is None:
        fig, ax = plt.subplots()
    keys = x.keys()
    vals = x.values()
    for l, y in ys.items():
         ax.scatter(vals, [y[k] for k in keys], c=c_it.next(), label=l)    
    ax.set_xlim(0, max(vals))
    ax.set_ylim(0)
    if (max(vals) > 1e2):
        ax.get_xaxis().get_major_formatter().set_powerlimits((0, 1))
    if (max([max(y) for y in ys.values()]) > 1e2):
        ax.get_yaxis().get_major_formatter().set_powerlimits((0, 1))    
    return ax    

def plot_xy(props, xhandle, yvals):
    vals = {x['instid']: x[xhandle] for x in props.iterrows()}
    
    m_it = imarkers()
    c_it = icolors()

    plts = {}
    solvers = sorted(yvals.keys())
    for s in solvers:
        l = yvals[s]
        x = [vals[i[0]] for i in l]
        y = [i[1] for i in l]
        plts[s] = plt.scatter(x, y, c=c_it.next(), marker=m_it.next(), label=s)    
    plt.xlim(0)
    plt.ylim(0)

    # Put a legend to the right of the current axis
    # Shrink current axis's height by 10% on the bottom
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend([plts[s] for s in solvers], solvers, loc='center left', 
              bbox_to_anchor=(1, 0.5))
    return ax

def plot_xyz(xtbl, xhandle, ytbl, yhandle, zvals, toinst=None, fromkey=None):
    xvals = {x['instid']: x[xhandle] for x in xtbl.iterrows()}
    if toinst is None:
        yvals = {x['instid']: x[yhandle] for x in ytbl.iterrows()}
    else:
        yvals = {toinst[x[fromkey]]: x[yhandle] for x in ytbl.iterrows()}
    
    m_it = imarkers()
    c_it = icolors()

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    plts = {}
    proxy = {}
    solvers = sorted(zvals.keys())
    minx, maxx = sys.float_info.max, sys.float_info.min
    miny, maxy = sys.float_info.max, sys.float_info.min
    minz, maxz = sys.float_info.max, sys.float_info.min
    for s in solvers:
        l = zvals[s]
        x = [xvals[i[0]] for i in l]
        minx = min(x) if min(x) < minx else minx
        maxx = max(x) if max(x) > maxx else maxx
        y = [yvals[i[0]] for i in l]
        miny = min(y) if min(y) < miny else miny
        maxy = max(y) if max(y) > maxy else maxy
        z = [i[1] for i in l]
        minz = min(z) if min(z) < minz else minz
        maxz = max(z) if max(z) > maxz else maxz
        c = c_it.next()
        m = m_it.next()
        plts[s] = ax.scatter(x, y, z, c=c, marker=m, label=s)  
        proxy[s] = lines.Line2D([0],[0], linestyle="none", c=c, marker=m)
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_zlim(minz, maxz)

    # Put a legend to the right of the current axis
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])  
    ax.legend([proxy[s] for s in solvers], solvers, loc='center left', 
              bbox_to_anchor=(1, 0.5))
    return ax
