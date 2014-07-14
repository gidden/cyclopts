import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as lines

def imarkers():
    return iter(['x', 's', 'o'])

def icolors():
    return iter(['g', 'b', 'r'])


def plot_xy(props, xhandle, yvals):
    vals = {x['instid']: x[xhandle] for x in props.iterrows()}
    
    m_it = imarkers()
    c_it = icolors()

    plts = {}
    for s, l in yvals.iteritems():
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
    ax.legend([p for _, p in plts.items()], [s for s, _ in plts.items()], 
              loc='center left', bbox_to_anchor=(1, 0.5))

def plot_xyz(xtbl, xhandle, ytbl, yhandle, zvals):
    xvals = {x['instid']: x[xhandle] for x in xtbl.iterrows()}
    yvals = {x['instid']: x[yhandle] for x in ytbl.iterrows()}
   
    m_it = imarkers()
    c_it = icolors()

    fig = plt.figure()
    ax = plt.axes(projection='3d')
    plts = {}
    proxy = {}
    for s, l in zvals.iteritems():
        x = [xvals[i[0]] for i in l]
        y = [yvals[i[0]] for i in l]
        z = [i[1] for i in l]
        c = c_it.next()
        m = m_it.next()
        plts[s] = ax.scatter(x, y, z, c=c, marker=m, label=s)  
        proxy[s] = lines.Line2D([0],[0], linestyle="none", c=c, marker=m)
    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.set_zlim(0)

    # Put a legend to the right of the current axis
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])  
    ax.legend([p for _, p in proxy.items()], [s for s, _ in plts.items()], 
              loc='center left', bbox_to_anchor=(1, 0.5))
    
    return ax
