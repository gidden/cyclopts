import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as lines
import matplotlib.markers as markers
from matplotlib.colors import colorConverter
import sys
from collections import defaultdict
from pylab import asarray
import tables as t
import os
import numpy as np
import inspect
import itertools as itools
from itertools import chain, izip, cycle

import cyclopts.cyclopts_io as cycio
import cyclopts.io_tools as io_tools
import cyclopts.tools as tools
from cyclopts.functionals import rms

def find(a, predicate, chunk_size=1024):
    """
    Find first index of occurance given a predicate, e.g., `next(find(a,
    lambda a: a > 4))`. 

    This was taken directly from https://github.com/numpy/numpy/issues/2269.
    """
    if a.ndim != 1:
        raise ValueError('The array must be 1D, not {}.'.format(a.ndim))

    i0 = 0
    chunk_inds = chain(xrange(chunk_size, a.size, chunk_size), 
                 [None])

    for i1 in chunk_inds:
        chunk = a[i0:i1]
        for inds in izip(*predicate(chunk).nonzero()):
            yield (inds[0] + i0, ), chunk[inds]
        i0 = i1

def imarkers():
    """Cycle through markers that arent skinny or none"""
    bad = range(4) + [None, '', ' ', 'None', ',', '.', '|', '_', 'x']
    return cycle([x for x in markers.MarkerStyle.markers.keys() \
                      if x not in bad])

def icolors():
    return cycle(['g', 'b', 'r', 'm', 'c', 'y'])

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

_ax_labels = {
    'n_arcs': 'Number of Arcs',
    'n_constrs': 'Number of Constraints',
    'n_u_grps': 'Number of Request Groups',
    'n_v_grps': 'Number of Supply Groups',
    'pref_flow': 'Product of Preference and Flow',
    'time': 'Time (s)',
    'obj': 'Objective Value',
    'objective': 'Objective Value',
    }

_legends = {
    'f_fc': ['Once Through', 'MOX Recycle', 'THOX/MOX Recycle'],
    'f_loc': ['None', 'Region', 'Region + Location'],
}

def add_limit_line(ax, x, y):
    ax.plot(x, y, c=plt.get_cmap('Greys')(0.75), linestyle='--')

class Plot(object):    
    def __init__(self, id_to_x, id_to_y, above=None, below=None):
        self.id_to_x = id_to_x
        self.id_to_y = id_to_y
        self.restrict = above is not None or below is not None
        if self.restrict and above is None and below is None:
            raise RuntimeError('Cannot specify below and above.')
        self.maskfunc = np.ma.masked_less if below is not None \
            else np.ma.masked_greater
        self.lim = above if above is not None else below
        self._data = None
        self._plot = None

    def _generate_data(self):
        ids = np.array(self.id_to_x.keys())
        x = np.array(self.id_to_x.values())
        y = np.array([self.id_to_y[_] for _ in ids])
        if self.restrict:
            mask = self.maskfunc(y, self.lim).mask
            if isinstance(mask, np.bool_): # true if all are below or above
                if not mask:
                    return [], [], []
            else:
                ids = ids[mask]
                x = x[mask]
                y = y[mask]
        return ids, x, y

    def _generate_plot(self, ax=None, id_to_color=None, addline=False, **kwargs):
        ids, x, y = self.data()
        fig, ax = plt.subplots() if ax is None else (None, ax)
        lim = 3 * 60 * 60 # 3 hour limit
        if addline and len(y) > 0 and max(y) > lim:
            add_limit_line(ax, x, len(x) * [lim])
        if id_to_color is not None:
            kwargs['c'] = [id_to_color[k] for k in ids]
        if 'c' not in kwargs:
            kwargs['c'] = ipastels().next()
        ax.scatter(x, y, **kwargs)
        return fig, ax

    def data(self):
        if self._data is None:
            self._data = self._generate_data()
        return self._data

    def plot(self, *args, **kwargs):
        if self._plot is None:
            self._plot = self._generate_plot(*args, **kwargs)
        return self._plot
    

        
"""A utility class for analyzing Cyclopts output"""
class Context(object):

    def __init__(self, fname, fam_mod, fam_cls, sp_mod, sp_class, save=False, savepath='.', show=True):
        import importlib
        self.fam_mod = importlib.import_module(fam_mod)
        self.fam_cls = getattr(self.fam_mod, fam_cls)
        self.sp_mod = importlib.import_module(sp_mod)
        self.sp_cls = getattr(self.sp_mod, sp_class)
        self.data = cyclopts_data(fname, self.fam_cls(), self.sp_cls())

        self.f = t.open_file(fname, mode='r')
        self.save = save
        self.savepath = savepath
        self.show = show

        res_path = cycio.PathMap().path
        self.instids = set(io_tools.grab_data(self.f, res_path, 'instid'))
        self.solvers = ['cbc', 'greedy', 'clp']
        self.times = {
            s: io_tools.grab_data(self.f, res_path, 'time', 
                                  ('solver', [s])) for s in self.solvers
            }
        self.objs = {
            s: io_tools.grab_data(self.f, res_path, 'objective', 
                                  ('solver', [s])) for s in self.solvers
            }

    def __del__(self):
        self.f.close()
        

    # these save/show functions need to be combined/refactor
    def _do_save(self, fig, save, fname):
        if self.save and save:
            fig.savefig(os.path.join(self.savepath, fname))

    def _save_and_show(self, fig, save, fname, show):
        if fig is None:
            self._plt_save_and_show(save, fname, show)
            return

        if self.save and save:
            fig.savefig(fname)
        if show:
            fig.show()

    def _set_power_limits(self, x, y, ax):
        if len(x) > 0 and max(x) > 1e3:
            ax.get_xaxis().get_major_formatter().set_powerlimits((0, 1))
        if len(y) > 0 and max(y) > 1e3:
            ax.get_yaxis().get_major_formatter().set_powerlimits((0, 1))

    def _plt_save_and_show(self, save, fname):
        if self.save and save:
            plt.savefig(fname)
        if show:
            plt.show()

    def _dress(self, x, y, ax, title=None, labels=None, reset_limits=False):
        if labels is not None:
            ax.set_xlabel(labels[0])
            ax.set_ylabel(labels[1])
        if title is not None:
            ax.set_title(title)
        if reset_limits:
            ax.set_xlim(0, 0)
            ax.set_ylim(0, 0)
        _, xmax = ax.get_xlim()
        xmin = 0
        if len(x) > 0:
            xmax = xmax if max(x) < xmax else max(x)
        ax.set_xlim(xmin, xmax)
        _, ymax = ax.get_ylim()
        ymin = 0
        if len(y) > 0:
            ymax = ymax if max(y) < ymax else max(y)
        ax.set_ylim(ymin, ymax)
        self._set_power_limits(x, y, ax)

    def _id_maps(self, param, solver, ykind, colorparam=None):
        xpmap = self.fam_mod.PathMap(param)
        id_to_x = io_tools.grab_data(self.f, xpmap.path, xpmap.col, 
                                     ('instid', self.instids))
        if ykind == 'time':
            id_to_y = self.times[solver]
        elif ykind == 'obj':
            id_to_y = self.objs[solver]
        id_to_color = None
        if colorparam is not None:
            c_it = ipastels()
            to_iids = io_tools.param_to_iids(
                self.f, self.fam_mod.PathMap(param).path, 
                self.sp_mod.PathMap(colorparam).path, colorparam)
            color_map = {k: c_it.next() for k in to_iids.keys()}
            id_to_color = {iid: color_map[k] for k, v in to_iids.items() for iid in v}
        return id_to_x, id_to_y, id_to_color
        
    def _filter_kwargs(self, kwargs, func):
        """returns kwargs only applicable to a function"""
        spec = inspect.getargspec(func)
        if spec.keywords is not None:
            return kwargs
        return {k: v for k, v in kwargs.items() if k in spec.args[-len(spec.defaults):]}

    def scatter(self, param, solver, ykind='time', colorparam=None, ax=None, 
                labels=True, dataonly=False,
                save=False, show=True, lim=None, where=None, title=None, 
                **kwargs):
        """return an axis with scatter plot as well as the ids, x, and y
        values"""
        id_to_x, id_to_y, id_to_color = self._id_maps(param, solver, ykind, 
                                                      colorparam)
        fkwargs = self._filter_kwargs(kwargs, Plot.__init__)
        kwargs = {k: v for k, v in kwargs.items() if not k in fkwargs.keys()}
        plot = Plot(id_to_x, id_to_y, **fkwargs)
        ids, x, y = plot.data()
        if dataonly:
            return ids, x, y
        addline = ykind == 'time'
        reset_limits = ax is None
        fig, ax = plot.plot(ax=ax, addline=addline, id_to_color=id_to_color, 
                            **kwargs)
        labels = (_ax_labels[param], _ax_labels[ykind]) if labels else None
        self._dress(x, y, ax, title=title, labels=labels, 
                    reset_limits=reset_limits)
        if save:
            fname = os.path.join(
                self.savepath, '{param}_{kind}.{ext}'.format(
                    param=param, kind=solver, ext='png'))
            fig.savefig(fname)
        return fig, ax

    def multi_solver_scatter(self, param, ax=None, solvers=None, legend=True,
                             save=False, **kwargs):
        solvers = self.solvers if solvers is None else solvers
        fig, ax = plt.subplots() if ax is None else (None, ax)
        c_it = ipastels()
        for s in solvers:
            label = s if legend else None
            _, ax = self.scatter(param, s, ax=ax, c=c_it.next(), label=label, 
                                 **kwargs)
        ax.legend(loc=0)
        if save:
            fname = os.path.join(
                self.savepath, '{param}_{kind}.{ext}'.format(
                    param=param, kind=solver, ext='png'))
            fig.savefig(fname)
        return fig, ax

    def four_pane_scatter(self, param, save=False, title=None, saveall=False, **kwargs):
        solvers = self.solvers
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True)
        _, ax1 = self.multi_solver_scatter(param, ax=ax1, solvers=solvers, 
                                           save=False, legend=False, **kwargs)
        c_it = ipastels()
        axs = [ax2, ax3, ax4]
        for i, s in enumerate(solvers):
            _, axs[i] = self.scatter(param, s, ax=axs[i], c=c_it.next(), title=s, 
                                     save=False, **kwargs)
        fig.set_size_inches(1.5 * fig.get_size_inches())

        title = param if title is None else title
        plt.suptitle(title)

        # # add only one label for all subplots
        # ax = fig.add_axes( [0., 0., 1, 1] )
        # ax.set_axis_off()
        # ax.text( 
        #     .05, 0.5, "Time (s)", rotation='vertical',
        #      horizontalalignment='center', verticalalignment='center'
        #      )
        # ax.text( 
        #     0.5, .05, _ax_labels[param], horizontalalignment='center', verticalalignment='center'
        #     )
        if save:
            fname = os.path.join(self.savepath, 
                                 '{param}_4pane.{ext}'.format(param=param, ext='png'))
            fig.savefig(fname)

    def three_pane_colorparam(self, param, cparam, save=False, title=None, **kwargs):
        solvers = self.solvers
        fig, ((off, ax1), (ax2, ax3)) = plt.subplots(2, 2, sharex=True)
        off.axis('off')
        axs = [ax1, ax2, ax3]
        for i, s in enumerate(solvers):
            _, axs[i] = self.scatter(param, s, ax=axs[i], colorparam=cparam, 
                                     title=s, save=False, **kwargs)
        
        labels = _legends[cparam] if cparam in _legends.keys() else to_iids.keys() 
        c_it = ipastels()
        handles = [patches.Patch(color=c_it.next()) for _ in labels]
        # handles = [patches.Patch(color=color_map[x], label=solvers[i]) \
        #                for i, x in enumerate(color_map.keys())]
        fig.legend(handles=handles, labels=labels, loc=(0.2, 0.65))
        fig.set_size_inches(1.5 * fig.get_size_inches())
        title = cparam if title is None else title
        fig.suptitle(title)

        # # add only one label for all subplots
        # ax = fig.add_axes( [0., 0., 1, 1] )
        # ax.set_axis_off()
        # ax.text( 
        #     .05, 0.5, "Time (s)", rotation='vertical',
        #      horizontalalignment='center', verticalalignment='center'
        #      )
        # ax.text( 
        #     0.5, .05, _ax_labels[param], horizontalalignment='center', verticalalignment='center'
        #     )
        if save:
            fname = os.path.join(
                self.savepath, '{cparam}_{param}_color.{ext}'.format(
                    cparam=cparam, param=param, ext='png'))
            fig.savefig(fname)

    def solver_hist(self, solver, source, colorby=None, 
                    ax=None, title='', save=True, **kwargs):
        """Return figure and axis for histograms of solver data.
        
        Parameters
        ----------
        solver : string or list
            the solvers to include
        source : str
            the histogram source (e.g., time, objective)
        colorby : str, optional
            a parameter used to color the histogram
        ax : pyplot.Axes, optional
        title : str, optional
            a title for the histogram
        save : bool, optional
            an override switch to save or not save this graph
        kwargs : pyplot.Axes.hist kwargs
        """
        fig = None
        if not tools.seq_not_str(solver):
            solver = [solver]
        if ax is None:
            fig, ax = plt.subplots()

        c_it = ipastels()
        data = self.data
        for s in solver:
            data = reduce_eq(data, {'solver': s})
            if colorby is None:
                _, _, _ = ax.hist(data[source], color=c_it.next(), **kwargs)
            else:
                kinds = np.unique(data[colorby])
                for k in kinds:
                    idxs = np.where(data[colorby] == k)
                    _, _, _ = ax.hist(data[idxs][source], color=c_it.next(), 
                                      label=_legends[colorby][k], **kwargs)
        
        ax.set_ylabel('Number of Observations')
        ax.set_xlabel(_ax_labels[source])
        ax.set_title(title)

        fname = 'solverhist_{0}_{1}.png'.format(source, '_'.join(solver))
        self._do_save(fig, save, fname)
        
        return fig, ax

    def avg_std(self, solver, source, data=None, ax=None, title='', save=True, **kwargs):
        """Return figure and axis for the cumulative average and standard
        devation given solver data.
        
        Parameters
        ----------
        solver : string or list
            the solvers to include
        source : str
            the histogram source (e.g., time, objective)
        data : array-like
            a limited data set to use (e.g., ctx.data[myparam == value])
        ax : pyplot.Axes, optional
        kwargs : pyplot.Axes.hist kwargs
        """
        fig = None
        if not tools.seq_not_str(solver):
            solver = [solver]
        if ax is None:
            fig, ax = plt.subplots()

        data = data if data is not None else self.data
        for s in solver:
            data = reduce_eq(data, {'solver': s})
            a = np.copy(data[source])
            np.random.shuffle(a)
            x = np.arange(len(a))

            avg = np.array([np.average(a[:i  + 1]) for i in x])
            std = np.array([np.std(a[:i + 1]) for i in x])
            avg_std = np.array([np.std(avg[:i + 1]) for i in x])
            ax.plot(x, avg, label='avg', **kwargs)
            ax.plot(x, avg_std, label='std of avg', **kwargs)
            ax.plot(x, std, label='std', **kwargs)

        ax.legend(loc=0)
        ax.set_ylabel(_ax_labels[source])
        ax.set_xlabel('Number of Observations')
        ax.set_title(title)
        
        fname = 'avgstd_{0}_{1}.png'.format(source, '_'.join(solver))
        self._do_save(fig, save, fname)

        return fig, ax

# """A utility class for doing aggregate data analyses"""
# class AggContext(object):
#     def __init__(self, fname, fam_mod, fam_cls, sp_mod, sp_cls):
#         self.fam_cls, self.sp_cls = fam_and_sp_cls(fam_mod, fam_cls, sp_mod, sp_cls)
#         self.fname = fname
#         self.data = cyclopts_data(self.fname, fam_cls(), sp_cls())
        
#     def rms(self, reduce_dict=None, col='flow', 
#             pathbase='/Family/ResourceExchange/ExchangeInstSolutions'):
#         """return the root-mean-squared of all logical combinations of data"""
#         ret = {}
#         i_to_s = defaultdict(list)
#         reddata = reduce_eq(self.data, reduce_dict)
#         for x in reddata:
#             i_to_s[x['instid']].append(x['solnid'])
#         with t.open_file(self.fname, mode='r') as f:
#             for iid, sids in i_to_s.items():
#                 data = {sid: f.get_node('/'.join([pathbase, sid]))[col] \
#                             for sid in sids}
#                 combos = itools.combinations(sids, 2)
#                 for a, b in combos:
#                     ret[tuple(iid, a, b)] = funcs.rms(data[a] - data[b])
#         return ret            

"""A utility class for doing Ratio analyses"""
class RatioContext(object):
    def __init__(self, fnames, labels, fam_mod, fam_cls, sp_mod, sp_cls, 
                 savepath='.', saveprefix='', save=False, show=True, 
                 lim=10800):
        self.fnames = fnames
        self.labels = labels
        self.save = save
        self.show = show
        self.savepath = savepath
        self.saveprefix = saveprefix
        self.lim = lim
        # TODO rework context to use new cyclopts_data
        self.ctxs = [Context(f, fam_mod, fam_cls, sp_mod, sp_cls, 
                             save=save, savepath=savepath) for f in self.fnames]
        # new for histograms
        fam_cls, sp_cls = fam_and_sp_cls(fam_mod, fam_cls, sp_mod, sp_cls)
        self.data = [cyclopts_data(f, fam_cls(), sp_cls()) for f in self.fnames]

    def _do_save(self, fig, save, fname):
        if self.save and save:
            fig.savefig(os.path.join(self.savepath, self.saveprefix + fname))

    def count(self, param, solver, **kwargs):
        count = []
        for i, ctx in enumerate(self.ctxs):
            _, _, y = ctx.scatter(param, solver, dataonly=True, **kwargs)
            count.append(len(y))
        return count

    def ratio_scatter(self, param, solver, save=False, savename=None, **kwargs):
        fig, ax = plt.subplots()
        xs = [None] * len(self.fnames)
        ids = [None] * len(self.fnames)
        ys = [None] * len(self.fnames)
        c_it = ipastels()
        colors = [c_it.next() for i in range(len(self.fnames))]
        ymin, ymax = float('inf'), 0
        xmin, xmax = float('inf'), 0
        for i, ctx in enumerate(self.ctxs):
            ids[i], xs[i], ys[i] = ctx.scatter(param, solver, dataonly=True)
            _, ax = ctx.scatter(param, solver, ax=ax, c=colors[i], 
                                label=self.labels[i], **kwargs)
            xmax = max(xs[i]) if len(xs[i]) > 0 and max(xs[i]) > xmax else xmax
            xmin = min(xs[i]) if len(xs[i]) > 0 and min(xs[i]) < xmin else xmin
            ymax = max(ys[i]) if len(ys[i]) > 0 and max(ys[i]) > ymax else ymax
            ymin = min(ys[i]) if len(ys[i]) > 0 and min(ys[i]) < ymin else ymin
        trys = ['above', 'below']
        for x in trys:
            lim = x if x in kwargs and kwargs[x] is not None else float('inf') 
        ymin = 0 if ymin < lim else lim
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, 1.1 * ymax)
        ax.legend(loc=0)
        
        if save:
            fname = os.path.join(self.savepath, savename)
            fig.savefig(fname)

        return fig, ax

    def count_hist(self, solver, lim, save=True, savename='count_hist.png'):
        fig, ax = plt.subplots()
        nbelow = np.array(self.count('n_arcs', solver, below=lim))
        nabove = np.array(self.count('n_arcs', solver, above=lim))

        width = 0.35
        idx = np.arange(len(nbelow))
        c_it = ipastels()
        below = ax.bar(idx, nbelow, width, color=c_it.next())
        above = ax.bar(idx, nabove, width, color=c_it.next(), bottom=nbelow)
        ax.set_xticks(idx + width / 2.)
        ax.set_xticklabels(self.labels)
        ax.legend((below[0], above[0]), ('Below', 'Above'))
        ax.set_ylabel('Number')
        ax.set_ylim(0, 1.4 * (nbelow[0] + nabove[0]))

        if save:
            fname = os.path.join(self.savepath, savename)
            fig.savefig(fname)
        return fig, ax
            
    def popn_hist(self, solver='cbc', lim=None, idxs=[0, 1], 
                  splitkind='time', popkind='objective', zone='a', 
                  ax=None, save=True, **kwargs):
        fig = None
        lim = lim or self.lim
        label = '{0} vs. {1}'.format(self.labels[idxs[0]], self.labels[idxs[1]])
        if not tools.seq_not_str(zone):
            zone = [zone]
        if ax is None:
            fig, ax = plt.subplots()
            
        x, y = self.data[idxs[0]], self.data[idxs[1]]
        x, y = [x[x['solver'] == solver], y[y['solver'] == solver]]
        xs, ys = split_group_by(x, y, splitkind, lim, 'instid')
        toplt = [np.array((xs[i][popkind] - ys[i][popkind]) / xs[i][popkind]) * 100 \
                     for i in range(len(xs))]
        
        zone_to_idx = {'a': 0, 'b': 1, 'c': 2}
        for z in zone:
            label = label if len(zone) == 1 else label + ', {0}'.format(z)
            _, _, _ = ax.hist(toplt[zone_to_idx[z]], label=label, **kwargs)

        ax.set_title('{0} vs. {1}, {2} Population, Zone: {3}'.format(
                self.labels[idxs[0]], self.labels[idxs[1]], 
                popkind.capitalize(), ', '.join(zone)))
        ax.set_ylabel('Number of Observations')
        ax.set_xlabel('% Relative Difference')

        fname = 'pophist_{0}_{1}_{2}.png'.format(popkind, '_'.join(zone), solver)
        self._do_save(fig, save, fname)

        return fig, ax

    def group_popn_hist(self, popkind='objective', zone='a', 
                        ax=None, save=True, **kwargs):
        fig, ax = plt.subplots()
        all_idxs = list(itools.combinations(range(len(self.labels)), 2))
        for idxs in all_idxs:
            _, _ = self.popn_hist(popkind=popkind, zone=zone, idxs=idxs, 
                                  ax=ax, **kwargs)
        ax.legend(loc=0)
        ax.set_title('{0} Population, Zone: {1}'.format(popkind, zone))
        return fig, ax

def fam_and_sp_cls(fam_mod, fam_cls, sp_mod, sp_class):
    """return constructors for problem.Family and problem.Species"""
    import importlib
    return getattr(importlib.import_module(fam_mod), fam_cls), \
        getattr(importlib.import_module(sp_mod), sp_class)

def idx_map(h5file, fam, sp):
    """return a mapping from all unique ids to an index, where each index
    corresponds to a specific solution"""
    sids = set(io_tools.grab_data(h5file, '/Results', 'solnid'))
    soln_idxs = {sid: i for i, sid in enumerate(sids)}
    pid_to_iids = io_tools.param_mapping(
        h5file, '/'.join([fam.io_prefix, fam.property_table_name]), 
        'paramid', 'instid')
    iid_to_sids = io_tools.param_mapping(h5file, '/Results', 'instid', 'solnid')
    idx_map = defaultdict(list)
    for p, iids in pid_to_iids.items():
        for i in iids:
            for s in iid_to_sids[i]:
                 idx_map[p].append(soln_idxs[s])
                 idx_map[i].append(soln_idxs[s])
                 idx_map[s].append(soln_idxs[s])
    return idx_map

def Tree(): return defaultdict(Tree)
def subtrees(tree): 
    """iterate through a tree, yielding top-level values with their subtrees"""
    for k, v in tree.items(): # trees are dicts (for now), so this is simple
        yield k, v

def id_tree(data, nsoln_prune=None):
    """return a uuid tree, consisting of param id nodes, inst id nodes, and
    solution id nodes. inst id nodes where the number of solution nodes is not
    equal to the number of expected solutions are pruned.
    
    Parameters
    ----------
    data : array-like
        e.g., the output of cyclopts_data
    nsoln_prune : int, optional
        prune an instance node if the number of solution nodes != nsoln_prune
    """
    tree = Tree()
    for d in data:
        tree[d['paramid']][d['instid']][d['solnid']] = d['solver']
        
    if nsoln_prune is None:
        return tree

    # remove instance nodes if number of solutions doesn't match
    torm = [(pid, iid) for pid, pst in subtrees(tree) \
                for iid, ist in subtrees(pst) if len(ist) != nsoln_prune]
    for pid, iid in torm:
        tree[pid].pop(iid)
        if len(tree[pid]) == 0:
            tree.pop(pid)

    return tree

def nnodes(id_tree, lev=0):
    """return the number of nodes in an id tree at a given level"""
    ret = [0] * 4
    ret[0] = len(id_tree)
    for _, pst in subtrees(id_tree):
        ret[1] += len(pst)
        for _, ist in subtrees(pst):
            ret[2] += len(ist)
    return ret[lev]

def ninsts(id_tree):
    """return the number of instances in an id tree"""
    return nnodes(id_tree, lev=1)

def leaf_vals(id_tree):
    """return unique values of leaves in a tree (on a single DFS iteration)"""
    for param, pst in subtrees(id_tree):
        for iid, ist in subtrees(pst):
            return set([solver for _, solver in subtrees(ist)])

def cyclopts_data(fname, fam, sp):
    """Return an numpy.ndarray of all aggregate data in a Cyclopts HDF5 file. 
    
    Parameters
    ----------
    fname : str
        the name of the hdf5 file
    fam : Problem.Family instance
        an instance of the family used in the table
    sp : Problem.Species instance
        an instance of the species used in the table
    """
    h5file = t.open_file(fname, mode='r')
    tbl_descs = fam.summary_tbls + sp.summary_tbls + \
        [cycio.TblDesc('/Results', 'soln', 'solnid')]
    id_to_idxs = idx_map(h5file, fam, sp)
    nsolns = h5file.get_node('/Results').nrows
    dtypes = [h5file.get_node(x.path).dtype.descr for x in tbl_descs]
    dtype = list(set(sum((x for x in dtypes), [])))

    data = np.empty(shape=(nsolns,), dtype=dtype)
    for desc in tbl_descs:
        tbl = h5file.get_node(desc.path)
        keys = tbl.coltypes.keys()
        for row in tbl.read():
            idxs = id_to_idxs[row[desc.idcol]]
            for i in idxs:
                for k in keys:
                    data[i][k] = row[k]

    # hack because l_pref_flow doesn't include f_l_c
    if 'l_pref_flow' in data.dtype.fields.keys():
        data['l_pref_flow'] = data['pref_flow'] - data['c_pref_flow']
 
    h5file.close()
    return data

def value_split(a, col, lim):
    """Return an ndarray split given some limit. For example, 
    value_split(a, 'time', 500)

    returns [a1, a2] where all values of a1 have time <= 500, and all values of
    a2 have time > 500.
    """
    a.sort(order=col)
    try:
        idx = next(find(a, lambda a: a[col] > lim))[0][0]
    except StopIteration:
        idx = len(a)
    return a[:idx], a[idx:]

def cleanse(x, y, col):
    """If x or y have different col values, remove them.
    """
    xvals = set(x[col])
    yvals = set(y[col])
    xdiff = xvals.difference(yvals)
    ydiff = yvals.difference(xvals)
    if len(xdiff) > 0:
        xmask = np.array([_[col] in xdiff for _ in x], dtype=bool)
        x = np.delete(x, x[xmask])
    if len(ydiff) > 0:
        ymask = np.array([_[col] in ydiff for _ in y], dtype=bool)
        y = np.delete(y, y[ymask])
    return x, y

def split_group_by(x, y, col, lim, groupby, sortby=True):
    """Splits x and y into three sections each: x1, x2, x3 and y1, y2, y3. x1 is
    all below the limit, y3 is all above the limit. 
    """
    xs = value_split(x, col, lim)
    ys = value_split(y, col, lim)
    agrp = xs[0][groupby]
    bgrp = ys[1][groupby]
    xmask = np.array([_[groupby] in bgrp for _ in xs[1]], dtype=bool)
    ymask = np.array([_[groupby] in agrp for _ in ys[0]], dtype=bool)
    xret = [xs[0], xs[1][~xmask], xs[1][xmask]]
    yret = [ys[0][ymask], ys[0][~ymask], ys[1]]
    if sortby:
        for i in range(len(xret)):
            x, y = xret[i], yret[i]
            x.sort(order=groupby)
            y.sort(order=groupby)
            if len(x) != len(y):
                x, y = cleanse(x, y, groupby)
                xret[i] = x
                yret[i] = y
                
    return xret, yret

def reduce(a, d, op):
    """Returns a reduced array where all values given a key equate as True given
    an condition.
    
    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    op : operator to use, given the form f(a, b). See for example,
         https://docs.python.org/2/library/operator.html.
    """
    ret = a
    for k, v in d.items():
        ret = ret[op(ret[k], v)]
    return ret

def reduce_eq(a, d):
    """Returns a reduced array where all values given a key are equal to a given
    value.
    
    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    """
    ret = a
    for k, v in d.items():
        ret = ret[ret[k] == v]
    return ret
    
def reduce_gt(a, d):
    """Returns a reduced array where all values given a key are greater than to
    a given value.
    
    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    """
    ret = a
    for k, v in d.items():
        ret = ret[ret[k] > v]
    return ret
    
def reduce_lt(a, d):
    """Returns a reduced array where all values given a key are less than to
    a given value.

    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    """
    ret = a
    for k, v in d.items():
        ret = ret[ret[k] < v]
    return ret
    
def reduce_in(a, d):
    """Returns a reduced array where entries have values in a collection.

    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    """
    ret = a
    for k, v in d.items():
        mask = np.array([_[k] in v for _ in ret], dtype=bool)
        ret = ret[mask]
    return ret
    
def reduce_not_in(a, d):
    """Returns a reduced array where entries do not have values in a collection.

    Parameters
    ----------
    a : array-like
    d : dict-like, {column keys: column values}
    """
    ret = a
    for k, v in d.items():
        mask = np.array([_[k] in v for _ in ret], dtype=bool)
        ret = ret[~mask]
    return ret

def avg_std(data, col=None, maxn=None, add=['std of avg'], ax=None, **kwargs):            
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
    
    data = data if col is None else data[col]
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[:n])
    np.random.shuffle(a)
    x = np.arange(len(a))
    
    avg = np.array([np.average(a[:i  + 1]) for i in x])
    std = np.array([np.std(a[:i + 1]) for i in x])
    avg_std = np.array([np.std(avg[:i + 1]) for i in x])
    ax.plot(x, avg, label='avg', **kwargs)
    ax.plot(x, std, label='std', **kwargs)
    if 'std of avg' in add:
        ax.plot(x, avg_std, label='std of avg', **kwargs)
    
    return fig, ax

def plot_approach(data, vals=['avg'], col=None, maxn=None, ax=None, 
                  **kwargs):
    # vals=['avg', 'std', 'std of avg']
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
    
    data = data if col is None else data[col]
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[:n])
    np.random.shuffle(a)
    x = np.arange(len(a))
    
    if 'avg' in vals:
        avg = np.array([np.average(a[:i  + 1]) for i in x])
        ax.plot(x, avg, label='avg', **kwargs)
    if 'std' in vals:
        std = np.array([np.std(a[:i + 1]) for i in x])
        ax.plot(x, std, label='std', **kwargs)
    if 'std of avg' in vals:
        avg_std = np.array([np.std(avg[:i + 1]) for i in x])
        ax.plot(x, avg_std, label='std of avg', **kwargs)
    
    return fig, ax

def hist(data, col, maxn=None, ax=None, colorby=None, **kwargs):
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
        
    c_it = ipastels()
    if colorby is None:
        _, _, _ = ax.hist(data[col], color=c_it.next(), **kwargs)
    else:
        kinds = np.unique(data[colorby])
        for k in kinds:
            idxs = np.where(data[colorby] == k)
            _, _, _ = ax.hist(data[idxs][col], color=c_it.next(), 
                              label=_legends[colorby][k], **kwargs)        
            ax.legend(loc=0)
        
    return fig, ax

def approach_avg(data, col, maxn=None, fillpercent=None, ax=None, **kwargs):
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[col][:n])
    np.random.shuffle(a)
    x = np.arange(len(a))
    
    avg = np.average(a)
    avg_i = np.array([1 - np.average(a[:i + 1]) / avg for i in x])
    ax.plot(x, avg_i, **kwargs)
    
    if fillpercent is not None:
        ax.fill_between(x, [-fillpercent] * len(x), [fillpercent] * len(x), 
                        color='grey', alpha=0.2)

    return fig, ax

def approach_std(data, col, maxn=None, ax=None, **kwargs):
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[col][:n])
    np.random.shuffle(a)
    x = np.arange(len(a))[1:]
    
    std_i = np.array([np.std(a[:i + 1]) / np.average(a[:i + 1]) for i in x])
    ax.plot(x, std_i, **kwargs)
    
    return fig, ax
        
def data_to_average_limit(data, avg_col, limit, maxn=None):
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[:n])
    np.random.shuffle(a)
    x = np.arange(len(a))

    vals = a[avg_col]
    avg = np.average(vals)
    avg_i = np.array([1 - np.average(vals[:i + 1]) / avg for i in x])
    # traverse backwards until the first value is greater than the limit
    try:
        idx = next(i for i, v in reversed(list(enumerate(avg_i))) if abs(v) > limit)
    except StopIteration:
        idx = 0
    idx = max(idx, 1)

    return a[:idx]

def compare_plot(data, xcol, ycol, base, compare, labels=None, maxn=None, 
                 ax=None, **kwargs):
    fig = None
    if ax is None:
        fig, ax = plt.subplots()
        
    ds, xs, ys = compare_plot_data(data, xcol, ycol, base, compare, maxn=maxn)
        
    labels = labels or [', '.join('{0}: {1}'.format(k, v) for k, v in x.items()) \
                            for x in d]
    m = imarkers()
    for x, y, l in zip(xs, ys, labels):
        if 'marker' in kwargs:
            ax.plot(x, y, label=l, linestyle='', **kwargs)
        else:
            ax.plot(x, y, label=l, linestyle='', marker=m.next(), **kwargs)
        
    return fig, ax

def compare_plot_data(data, xcol, ycol, base, compare, maxn=None):
    n = min(maxn, len(data)) if maxn is not None else len(data)
    a = np.copy(data[:n])
    np.random.shuffle(a)
    x = np.arange(len(a))

    basedata = reduce_eq(a, base)
    xbase = np.average(basedata[xcol]) 
    ybase = np.average(basedata[ycol])
    xs = [0]
    ys = [0]
    
    for c in compare:
        d = reduce_eq(a, c)
        xs.append((np.average(d[xcol]) - xbase) / xbase)
        ys.append((np.average(d[ycol]) - ybase) / ybase)
        
    return [base] + compare, xs, ys

def flow_rms(fname, id_tree, species_name):
    """Take the root-mean-square of flow values of all solutions in an ID Tree.

    Parameters
    ----------
    fname : str
        the hdf5 file name
    id_tree : cyclopts.analysis.Tree
        e.g., from cyclopts.analysis.id_tree()
    species : str
        either 'StructuredRequest' or 'StructuredSupply'
    """
    cpath = '/Species/{}/Arcs'.format(species_name)
    fpath = '/Family/ResourceExchange/ExchangeInstSolutions'
    solvers = set(leaf_vals(id_tree))    
    n = ninsts(id_tree) 
    ret = {'flows': {s: np.zeros(n) for s in solvers},
           'cflows': {s: np.zeros(n) for s in solvers}}
    convert = lambda x: 'id_' + tools.str_to_uuid(x).hex 
    i = 0
    
    with t.open_file(fname, mode='r') as f:
        for pid, pst in subtrees(id_tree):
            for iid, ist in subtrees(pst):
                cprefs = f.get_node(cpath + '/' + convert(iid)).col('pref_c')
                for sid, solver in subtrees(ist):
                    flows = f.get_node(fpath + '/' + convert(sid)).col('flow')
                    ret['flows'][solver][i] = rms(flows)
                    ret['cflows'][solver][i] = rms(cprefs * flows)
                i += 1
    return ret

def flow_rms_diff(fname, id_tree, species_name, base_solver='cbc'):
    """Take the root-mean-square of the difference of flow values for all
    solutions in an ID Tree given a solver type.

    Parameters
    ----------
    fname : str
        the hdf5 file name
    id_tree : cyclopts.analysis.Tree
        e.g., from cyclopts.analysis.id_tree()
    species : str
        either 'StructuredRequest' or 'StructuredSupply'
    base_solver : str, optional
        the solver on which comparisons are made
    """
    cpath = '/Species/{}/Arcs'.format(species_name)
    fpath = '/Family/ResourceExchange/ExchangeInstSolutions'
    solvers = set(leaf_vals(id_tree)) - {base_solver}    
    n = ninsts(id_tree) 
    ret = {'flows': {s: np.zeros(n) for s in solvers},
           'cflows': {s: np.zeros(n) for s in solvers}}
    convert = lambda x: 'id_' + tools.str_to_uuid(x).hex 
    i = 0
    
    with t.open_file(fname, mode='r') as f:
        for pid, pst in subtrees(id_tree):
            for iid, ist in subtrees(pst):
                cprefs = f.get_node(cpath + '/' + convert(iid)).col('pref_c')
                flows = {
                    solver: f.get_node(fpath + '/' + convert(sid)).col('flow') \
                        for sid, solver in subtrees(ist)}
                for solver in solvers:
                    diff = flows[base_solver] - flows[solver]
                    ret['flows'][solver][i] = rms(diff)
                    ret['cflows'][solver][i] = rms(cprefs * diff)
                i += 1
    return ret

def rms_analysis(fname, data, kind='rms_diff', species_name='StructuredRequest',
                 nsoln_prune=None, base_solver='cbc'):
    """Return the results of an RMS analysis.

    Parameters
    ----------
    fname : str
        the hdf5 file name
    data : array-like
        e.g., the output of cyclopts_data
    kind : str, optional
        the kind of analysis ('rms_diff' or 'rms') 
    species_name : str, optional
        either 'StructuredRequest' or 'StructuredSupply'
    nsoln_prune : int, optional
        the expected number of solution nodes hanging on inst nodes, see 
        id_tree()
    base_solver : str, optional
        the solver on which comparisons are made, required if kind is 'rms_diff'
    """
    tree = id_tree(data, nsoln_prune=nsoln_prune)
    if kind == 'rms_diff':
        rms_vals = flow_rms_diff(fname, tree, species_name, base_solver)
    else:
        rms_vals = flow_rms(fname, tree, species_name)
    return rms_vals
