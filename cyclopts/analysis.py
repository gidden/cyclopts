import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as lines
from matplotlib.colors import colorConverter
import sys
from collections import defaultdict
from pylab import asarray
import tables as t
import os
import numpy as np

import cyclopts.cyclopts_io as cycio
import cyclopts.io_tools as io_tools

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
    'pref_flow': 'Product of Preference and Flow',
    }

_legends = {
    'f_fc': ['Once Through', 'MOX Recycle', 'THOX/MOX Recycle'],
    'f_loc': ['None', 'Region', 'Region + Location'],
}

def add_limit_line(ax, x, y):
    ax.plot(x, y, c=plt.get_cmap('Greys')(0.75), linestyle='--')

"""A utility class for doing Ratio analyses"""
class RatioContext(object):
    def __init__(self, fnames, labels, fam_mod, fam_cls, sp_mod, sp_cls, 
                 savepath='.', save=False, show=True, lim=10800):
        self.fnames = fnames
        self.labels = labels
        self.save = save
        self.show = show
        self.savepath = savepath
        self.lim = lim
        self.ctxs = [Context(f, fam_mod, fam_cls, sp_mod, sp_cls, 
                             save=save, savepath=savepath) for f in self.fnames]
        
    def _save_and_show(self, fig, save, fname, show):
        if fig is None:
            self._plt_save_and_show(save, fname, show)
            return

        if self.save and save:
            fig.savefig(fname)
        if show:
            fig.show()

    def _plt_save_and_show(self, save, fname, show):
        if self.save and save:
            plt.savefig(fname)
        if show:
            plt.show()

    def count(self, param, solver, where=None, **kwargs):
        count = []
        lim = None if where is None else self.lim
        for i, ctx in enumerate(self.ctxs):
            _, _, _, y = ctx.solver_scatter(
                param, solver, show=False, lim=lim, where=where, **kwargs)
            count.append(len(y))
        return count

    def ratio_scatter(self, param, solver, colors=None, where=None, savename=None, 
                      **kwargs):
        fig, ax = plt.subplots()
        xs = [None] * len(self.fnames)
        ids = [None] * len(self.fnames)
        ys = [None] * len(self.fnames)
        if colors is None:
            c_it = ipastels()
            colors = [c_it.next() for i in range(len(self.fnames))]
        lim = None if where is None else self.lim
        ymin, ymax = float('inf'), 0
        xmin, xmax = float('inf'), 0
        # update kwargs, only save top-level graph
        save = kwargs['save'] if 'save' in kwargs else False
        kwargs['save'] = False
        show = kwargs['show'] if 'show' in kwargs else False
        kwargs['show'] = False
        for i, ctx in enumerate(self.ctxs):
            _, ids[i], xs[i], ys[i] = ctx.solver_scatter(
                param, solver, ax=ax, lim=lim, where=where, color=colors[i], 
                label=self.labels[i], 
                **kwargs)
            xmax = max(xs[i]) if len(xs[i]) > 0 and max(xs[i]) > xmax else xmax
            xmin = min(xs[i]) if len(xs[i]) > 0 and min(xs[i]) < xmin else xmin
            ymax = max(ys[i]) if len(ys[i]) > 0 and max(ys[i]) > ymax else ymax
            ymin = min(ys[i]) if len(ys[i]) > 0 and min(ys[i]) < ymin else ymin
        ymin = 0 if ymin < lim else lim
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, 1.1 * ymax)
        ax.legend(loc=0)
        self._save_and_show(fig, save, savename, show)
        return fig, ax

"""A utility class for analyzing Cyclopts output"""
class Context(object):

    def __init__(self, fname, fam_mod, fam_cls, sp_mod, sp_class, save=False, savepath='.', show=True):
        import importlib
        self.fam_mod = importlib.import_module(fam_mod)
        self.fam_cls = getattr(self.fam_mod, fam_cls)
        self.sp_mod = importlib.import_module(sp_mod)
        self.sp_cls = getattr(self.sp_mod, sp_class)
        self.f = t.open_file(fname, mode='r')
        self.save = save
        self.savepath = savepath
        self.show = show

        res_path = cycio.PathMap().path
        self.instids = set(io_tools.grab_data(self.f, res_path, 'instid'))
        self.solvers = ['greedy', 'clp', 'cbc']
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
        
    def _save_and_show(self, fig, save, fname, show):
        if fig is None:
            self._plt_save_and_show(save, fname, show)
            return

        if self.save and save:
            fig.savefig(fname)
        if show:
            fig.show()

    def _set_power_limits(self, x, y, ax):
        if (max(x) > 1e3):
            ax.get_xaxis().get_major_formatter().set_powerlimits((0, 1))
        if (max(y) > 1e3):
            ax.get_yaxis().get_major_formatter().set_powerlimits((0, 1))

    def _plt_save_and_show(self, save, fname, show):
        if self.save and save:
            plt.savefig(fname)
        if show:
            plt.show()

    def simple_scatter(self, x, param, solver, color=None, ax=None, labels=True, 
                       save=False, show=True, lim=None, where=None, title=None, 
                       **kwargs):
        """return an axis with scatter plot as well as the ids, x, and y
        values"""
        fig = None
        if ax is None:
            fig, ax = plt.subplots()
        ids = np.array(x.keys())
        x = np.array(x.values())
        y = np.array([self.times[solver][k] for k in ids])
        if lim is not None:
            if where is None:
                raise RuntimeError('Lim and Where must both be specified')
            mfunc = np.ma.masked_less if where == 'below' else np.ma.masked_greater
            mask = mfunc(y, lim).mask
            if isinstance(mask, np.bool_): # true if all are below or above
                if not mask:
                    return ax, [], [], []
            else:
                ids = ids[mask]
                x = x[mask]
                y = y[mask]
        else:
            lim = 3 * 60 * 60 # 3 hour limit
            if max(y) > lim:
                add_limit_line(ax, x, len(x) * [lim])
        color = icolors().next() if color is None else color
        ax.scatter(x, y, c=color, **kwargs)
        ax.set_xlim(0)#, max(x))
        ax.set_ylim(0)
        if labels:
            ax.set_xlabel(_ax_labels[param])
            ax.set_ylabel('Time (s)')
        title = solver if title is None else title
        ax.set_title(title)
        self._set_power_limits(x, y, ax)

        fname = os.path.join(
            self.savepath, '{param}_{kind}.{ext}'.format(
                param=param, kind=solver, ext='png'))
        self._save_and_show(fig, save, fname, show)
        return ax, ids, x, y

    def solver_scatter(self, param, solver, **kwargs):
        xpmap = self.fam_mod.PathMap(param)
        id_to_x = io_tools.grab_data(self.f, xpmap.path, xpmap.col, 
                                     ('instid', self.instids))
        ax, ids, x, y = self.simple_scatter(id_to_x, param, solver, labels=True, **kwargs)
        return ax, ids, x, y

    def all_scatter(self, param, colors=None, ax=None, save=False, show=True):
        xpmap = self.fam_mod.PathMap(param)
        x = io_tools.grab_data(self.f, xpmap.path, xpmap.col, ('instid', self.instids))
        ax = multi_scatter(x, self.times, colors=colors, ax=ax)
        lim = [3 * 60 * 60] # 3 hour limit
        add_limit_line(ax, x.values(), len(x) * lim)
        ax.set_title('all')
        #ax.set_xlabel(param)
        #ax.set_ylabel('Time (s)')
        fname = os.path.join(self.savepath, '{param}_all.{ext}'.format(param=param, ext='png'))
        #self._save_and_show(save, fname, False)
        return x, ax

    def four_pane_scatter(self, param, saveall=False, title=None, **kwargs):
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex=True)
        x, ax1 = self.all_scatter(param, colors=ipastels(), ax=ax1, save=False, show=False)
        kinds = ['cbc', 'greedy', 'clp']
        c_it = ipastels()
        axs = [ax2, ax3, ax4]
        for i in range(len(kinds)):
            axs[i], _, _, _ = self.simple_scatter(x, param, kinds[i], color=c_it.next(), ax=axs[i], labels=False, save=False, **kwargs)
        fig.set_size_inches(1.5 * fig.get_size_inches())

        title = cparam if title is None else title
        plt.suptitle(title)

        # add only one label for all subplots
        ax = fig.add_axes( [0., 0., 1, 1] )
        ax.set_axis_off()
        ax.text( 
            .05, 0.5, "Time (s)", rotation='vertical',
             horizontalalignment='center', verticalalignment='center'
             )
        ax.text( 
            0.5, .05, _ax_labels[param], horizontalalignment='center', verticalalignment='center'
            )
        fname = os.path.join(self.savepath, '{param}_4pane.{ext}'.format(param=param, ext='png'))
        self._save_and_show(fig, save, fname, show)
        
        if saveall:
            self.all_scatter(param, colors=ipastels(), save=saveall, show=False)
            plt.close()
            c_it = ipastels()
            for i in range(len(kinds)):
                self.simple_scatter(x, param, kinds[i], color=c_it.next(), labels=False, save=saveall, show=show)
                plt.close()

    def colored_scatter(self, x, kind, id_mapping, color_map, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        lim = 3 * 60 * 60 # 3 hour limit
        if max(self.times[kind].values()) > lim:
            add_limit_line(ax, x.values(), len(x) * [lim])
        ax.scatter(x.values(), [self.times[kind][k] for k in x.keys()], c=[color_map[id_mapping[k]] for k in x.keys()])
        ax.set_xlim(0, max(x.values()))
        ax.set_ylim(0)
        if (max(x) > 1e3):
            ax.get_xaxis().get_major_formatter().set_powerlimits((0, 1))
        if (max(self.times[kind].values()) > 1e3):
            ax.get_yaxis().get_major_formatter().set_powerlimits((0, 1))
        return ax 

    def three_pane_color_scatter(self, param, cparam, famparam='n_arcs', 
                                 title=None, save=False, show=True):
        to_iids = io_tools.param_to_iids(
            self.f, self.fam_mod.PathMap(famparam).path, 
            self.sp_mod.PathMap(cparam).path, cparam)
        id_mapping = {iid: k for k, v in to_iids.items() for iid in v}
        xpmap = self.fam_mod.PathMap(param)
        x = io_tools.grab_data(self.f, xpmap.path, xpmap.col, ('instid', self.instids))
        fig, ((off, ax1), (ax2, ax3)) = plt.subplots(2, 2, sharex=True)
        off.axis('off')
        axs = [ax1, ax2, ax3]
        kinds = ['cbc', 'greedy', 'clp']
        c_it = ipastels()
        color_map = {k: c_it.next() for k in to_iids.keys()}
        for i in range(len(kinds)):
            ax = self.colored_scatter(x, kinds[i], id_mapping, color_map, ax=axs[i])
            ax.set_title(kinds[i].capitalize())
        handles = [patches.Patch(color=color_map[x], label=kinds[i]) for i, x in enumerate(color_map.keys())]
        labels = _legends[cparam] if cparam in _legends.keys() else to_iids.keys() 
        fig.legend(handles=handles, labels=labels, loc=(0.2, 0.65))
        fig.set_size_inches(1.5 * fig.get_size_inches())
        title = cparam if title is None else title
        plt.suptitle(title)

        # add only one label for all subplots
        ax = fig.add_axes( [0., 0., 1, 1] )
        ax.set_axis_off()
        ax.text( 
            .05, 0.5, "Time (s)", rotation='vertical',
             horizontalalignment='center', verticalalignment='center'
             )
        ax.text( 
            0.5, .05, _ax_labels[param], horizontalalignment='center', verticalalignment='center'
            )
        fname = os.path.join(self.savepath, '{cparam}_{param}_color.{ext}'.format(cparam=cparam, param=param, ext='png'))
        self._save_and_show(fig, save, fname, show)

