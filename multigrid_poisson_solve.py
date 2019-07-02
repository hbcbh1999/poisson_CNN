import pyamg
import tensorflow as tf
import numpy as np
import copy
import itertools
from collections.abc import Iterator

def poisson_RHS(F, boundaries = None, h = None, rho = None):
    boundaries = copy.deepcopy(boundaries)
    
    rhs = np.zeros(F.shape)#np.zeros(list(F.shape[:-2]) + [np.prod(F.shape[-2:])])
      
    for key in boundaries.keys():
        if len(boundaries[key].shape) > 1:
            boundaries[key] = tf.squeeze(boundaries[key])
        if len(boundaries[key].shape) == 1:
            boundaries[key] = itertools.repeat(boundaries[key], F.shape[0])
    
    if (h is not None) and isinstance(h, float):
        h = itertools.repeat(h, F.shape[0])
      
    for i in range(F.shape[0]):
        if h is not None:
            try:
                dx = next(h)
            except:
                dx = h[i]
            F[i] = -dx**2 * F[i]
      
        if isinstance(boundaries['top'], Iterator):
            top = next(boundaries['top'])
        else:
            top = boundaries['top'][i]
            
        if isinstance(boundaries['bottom'], Iterator):
            bottom = next(boundaries['bottom'])
        else:
            bottom = boundaries['bottom'][i]
            
        if isinstance(boundaries['left'], Iterator):
            left = next(boundaries['left'])
        else:
            left = boundaries['left'][i]
            
        if isinstance(boundaries['right'], Iterator):
            right = next(boundaries['right'])
        else:
            right = boundaries['right'][i]
        
      
        rhs[i,...,0] = top
        rhs[i,...,-1] = bottom
        rhs[i,...,0,:] = left
        rhs[i,...,-1,:] = right
        rhs[i,...,1:-1,1:-1] = F[i,...,1:-1,1:-1]
      
    return rhs.reshape(list(rhs.shape[:-2]) + [np.prod(rhs.shape[-2:])])

def multigrid_poisson_solve(rhses, boundaries, dx, dy = None, system_matrix = None, tol = 1e-10):

    try:
        rhses = rhses.numpy()
    except:
        pass
    
    if rhses.shape[1] == 1:
        rhses = np.squeeze(rhses, axis = 1)
    
    solns = np.zeros([rhses.shape[0] , np.prod(rhses.shape[1:])])
    rhs_vectors = poisson_RHS(rhses, boundaries, h = dx)

    if system_matrix == None:
        system_matrix = pyamg.gallery.poisson(rhses.shape[1:], format = 'csr')
    solver = pyamg.ruge_stuben_solver(system_matrix)
    print(system_matrix.shape)
    
    for k in range(rhses.shape[0]):
        solns[k,...] = solver.solve(np.squeeze(rhs_vectors[k,...]), tol = tol)
        

    return np.expand_dims(np.reshape(solns, rhses.shape, order = 'f'), axis = 1)
    
