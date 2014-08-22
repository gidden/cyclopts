"""This module defines a ProblemSpecies subclass and related classes for
reactor-request-based resources exchanges that model a 4-commodity, fast/thermal
reactor case. For extensive documentation, see the
[docs](http://mattgidden.com/cyclopts/theory/f_th_reactor_request.html).

:author: Matthew Gidden <matthew.gidden _at_ gmail.com>
"""
import math

from collections import namedtuple

Request = namedtuple('Request', ['commod', 'qty', 'enr'])

def reg_pref(r1, r2):
    """Return a regional preference score"""
    return math.exp(math.abs(r2 - r1))

def loc_pref(l1, l2):
    """Return a locational preference score"""
    return math.exp(abs(l2 - l1))

def pref(arc, fine=False):
    """return an arc's prefernce value"""
    if fine:
        return 0.5 * (reg_pref(arc.r1, arc.r2) + loc_pref(arc.l1, arc.l2))
    else:
        return reg_pref(arc.r1, arc.r2)
