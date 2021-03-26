import numpy as np
import rasterio
import scipy.interpolate as spint
import matplotlib.pylab as plt

# -------------------------------------------------------------------------------------
# Method to regrid raster
def regrid_raster(static_obj, DEM_obj):

    #Get XYZ of layer to be resampled
    X_current = np.reshape(static_obj['longitude'], (np.product(static_obj['longitude'].shape), 1), order='C')
    Y_current = np.reshape(static_obj['latitude'], (np.product(static_obj['latitude'].shape), 1), order='C')
    Z_current = static_obj['values']

    #Get XY of DEM
    grid_x = DEM_obj['longitude']
    grid_x = np.transpose(grid_x)
    grid_x_reshaped= np.reshape(grid_x, (np.product(grid_x.shape), 1), order='C')

    grid_y = DEM_obj['latitude']
    grid_y = np.flip(np.transpose(grid_y),0)
    grid_y_reshaped= np.reshape(grid_y, (np.product(grid_y.shape), 1), order='C')

    #resample
    grid_z0 = spint.griddata(np.concatenate((X_current, Y_current), axis=1),
                                       np.reshape(Z_current, (np.product(Z_current.shape), 1),
                                                  order='C'), np.concatenate((grid_x_reshaped, grid_y_reshaped), axis=1),
                                       method='nearest')
    grid_z0_reshaped = np.transpose(np.reshape(grid_z0, (grid_x.shape), order='C'))

    plt.imshow(grid_z0_reshaped)
    plt.show()

    obj = {'values': grid_z0_reshaped, 'longitude': grid_x, 'latitude': grid_y,}

    return obj

