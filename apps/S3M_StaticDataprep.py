"""
Flood-Proofs - S3M static-data prep
__date__ = '20211213'
__version__ = '2.0.0'
__author__ = 'Francesco Avanzi (francesco.avanzi@cimafoundation.org',
             'Fabio Delogu (fabio.delogu@cimafoundation.org',
__library__ = 's3m'
General command line:
python3 S3M_StaticDataprep.py -settings_file "S3M_StaticDataprep_configuration.json"
"""

# -------------------------------------------------------------------------------------
# Complete library
import os
import json
import numpy as np
import pandas as pd
from netCDF4 import Dataset
from argparse import ArgumentParser
from src.s3m_geotools.S3M_geotools import regrid_raster
from src.s3m_io.S3M_io import get_file_raster

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'FP S3M STATIC-DATA PREPARATION TOOL'
alg_version = '1.1.0'
alg_release = '2021-02-15'

# -------------------------------------------------------------------------------------
# Script Main
def main():
    # -------------------------------------------------------------------------------------
    # Get script arguments
    file_config = get_args()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    with open(file_config, "r") as file_handle:
        file_data = json.load(file_handle)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Open DEM, load and optionally resample it
    DEM_file_name = os.path.join(file_data['static_data_path'], file_data['DEM_name'])
    DEM_obj = get_file_raster(DEM_file_name)
    xllcorner_forNC = DEM_obj['bb_left']
    yllcorner_forNC = DEM_obj['bb_bottom']
    cellsize_forNC = DEM_obj['res_lon']
    nodata_value_forNC = file_data['nodata_value']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Use this DEM to initialize & populate NC file
    NetCDF_full_path = os.path.join(file_data['static_data_output_path'], file_data['static_data_output_name'])
    ds = Dataset(NetCDF_full_path, 'w', format='NETCDF4')

    # # compute and initialize dimensions
    Size_static = np.shape(DEM_obj['values'])
    Y_dim = ds.createDimension('Y', Size_static[0])
    X_dim = ds.createDimension('X', Size_static[1])
    time = ds.createDimension('time', 1)

    # create default variables + DEM
    crs = ds.createVariable("crs", "i", ("time",))
    Longitude = ds.createVariable("Longitude", "d", ("Y", "X",))
    Latitude = ds.createVariable("Latitude", "d", ("Y", "X",))
    Terrain = ds.createVariable("Terrain", "f", ("Y", "X",))

    # Set global attributes
    ds.filename = file_data['static_data_output_name']
    ds.domainname = file_data['domain']
    ds.nodata_value = -9999
    ds.comment = "Author(s): Francesco Avanzi, Fabio Delogu"
    ds.project = file_data['project']
    ds.website = "http://www.cimafoundation.org"
    ds.institution = "CIMA Research Foundation "
    ds.algorithm = "S3M"
    ds.title = "S3M, Static Data"
    ds.email = "francesco.avanzi@cimafoundation.org"
    ds.xllcorner = xllcorner_forNC
    ds.yllcorner = yllcorner_forNC
    ds.cellsize = cellsize_forNC
    ds.nodata_value = nodata_value_forNC
    ds.nrows = int(np.shape(DEM_obj['values'])[0])
    ds.ncols = int(np.shape(DEM_obj['values'])[1])

    # attributi crs
    crs.bounding_box = []
    crs.inverse_flattening = 298.2572
    crs.longitude_of_prime_meridian = 0
    crs.grid_mapping_name = "latitude_longitude"
    crs.semi_major_axis = 6378137

    # attributi longitude
    Longitude[:] = DEM_obj['longitude']
    Longitude.long_name = 'longitude coordinate'
    Longitude.standard_name = 'longitude_grid'
    Longitude.units = 'degrees_east'
    Longitude.scale_factor = 1

    # attributi latitude
    Latitude[:] = np.flipud(DEM_obj['latitude'])
    Latitude.long_name = 'latitude coordinate'
    Latitude.standard_name = 'latitude_grid'
    Latitude.units = 'degrees_north'
    Latitude.scale_factor = 1

    # attributes terrain
    Terrain[:] = np.flipud(DEM_obj['values'])
    Terrain.grid_mapping = ''
    Terrain.coordinates = ''
    Terrain.cell_method = ''
    Terrain.pressure_level = ''
    Terrain.long_name = 'Terrain'
    Terrain.standard_name = 'Terrain'
    Terrain.units = 'm asl'
    Terrain.scale_factor = 1

    # Import (and optionally resample) glacier thickness
    if file_data['glacier_thickness']:
        Thickness_file_name = os.path.join(file_data['static_data_path'], file_data['Glacier_thickness_name'])
        Thickness_obj = get_file_raster(Thickness_file_name)

        if file_data['sim_regrid_on_DEM']:
            Thickness_obj = regrid_raster(Thickness_obj, DEM_obj)

        #write
        Thickness = ds.createVariable("Thickness", "f", ("Y", "X",))

        # attributes thickness
        Thickness[:] = np.flipud(Thickness_obj['values'])
        Thickness.grid_mapping = ''
        Thickness.coordinates = ''
        Thickness.cell_method = ''
        Thickness.pressure_level = ''
        Thickness.long_name = 'Thickness'
        Thickness.standard_name = 'Thickness'
        Thickness.units = 'm'
        Thickness.scale_factor = 1

    # Import (and optionally resample) glacier ID
    if file_data['glacier_ID']:
        GlacierID_file_name = os.path.join(file_data['static_data_path'], file_data['Glacier_ID_name'])
        GlacierID_obj = get_file_raster(GlacierID_file_name)

        if file_data['sim_regrid_on_DEM']:
            GlacierID_obj = regrid_raster(GlacierID_obj, DEM_obj)

        # write
        Glacier_ID = ds.createVariable("GlacierID", "f", ("Y", "X",))

        # attributes thickness
        Glacier_ID[:] = np.flipud(GlacierID_obj['values'])
        Glacier_ID.grid_mapping = ''
        Glacier_ID.coordinates = ''
        Glacier_ID.cell_method = ''
        Glacier_ID.pressure_level = ''
        Glacier_ID.long_name = 'Glacier_ID'
        Glacier_ID.standard_name = 'Glacier_ID'
        Glacier_ID.units = '-'
        Glacier_ID.scale_factor = 1

    # Import (and optionally resample) deltaH pivot table
    if file_data['deltaH_pivot_table']:
        deltaH_pivot_table = pd.read_table(
            os.path.join(file_data['static_data_path'], file_data['deltaH_pivot_table_name']), header=None)

        deltaH_pivot_table = np.transpose(deltaH_pivot_table)

        Rows_Pivot = ds.createDimension('ROW_PIVOT', np.shape(deltaH_pivot_table)[0])
        Columns_Pivot = ds.createDimension('COL_PIVOT', np.shape(deltaH_pivot_table)[1])

        # write
        PivotTable = ds.createVariable("PivotTable", "f", ("ROW_PIVOT", "COL_PIVOT",))

        # attributes thickness
        PivotTable[:] = deltaH_pivot_table
        PivotTable.grid_mapping = ''
        PivotTable.coordinates = ''
        PivotTable.cell_method = ''
        PivotTable.pressure_level = ''
        PivotTable.long_name = 'PivotTable_DeltaH'
        PivotTable.standard_name = 'PivotTable_DeltaH'
        PivotTable.units = '-'
        PivotTable.scale_factor = 1


    # Import (and optionally resample) AreaCell
    AreaCell_file_name = os.path.join(file_data['static_data_path'], file_data['Area_cell_name'])
    AreaCell_obj = get_file_raster(AreaCell_file_name)

    if file_data['sim_regrid_on_DEM']:
        AreaCell_obj = regrid_raster(AreaCell_obj, DEM_obj)

    # write
    AreaCell = ds.createVariable("AreaCell", "f", ("Y", "X",))

    # attributes AreaCell
    AreaCell[:] = np.flipud(AreaCell_obj['values'])
    AreaCell.grid_mapping = ''
    AreaCell.coordinates = ''
    AreaCell.cell_method = ''
    AreaCell.pressure_level = ''
    AreaCell.long_name = 'AreaCell'
    AreaCell.standard_name = 'AreaCell'
    AreaCell.units = 'm^2'
    AreaCell.scale_factor = 1

    # Import (and optionally resample) Domain Mask
    if file_data['mask']:
        Mask_file_name = os.path.join(file_data['static_data_path'], file_data['mask_name'])
        Mask_obj = get_file_raster(Mask_file_name)

        if file_data['sim_regrid_on_DEM']:
            Mask_obj = regrid_raster(Mask_obj, DEM_obj)

        # write
        Mask = ds.createVariable("Mask", "f", ("Y", "X",))

        # attributes AreaCell
        Mask[:] = np.flipud(Mask_obj['values'])
        Mask.grid_mapping = ''
        Mask.coordinates = ''
        Mask.cell_method = ''
        Mask.pressure_level = ''
        Mask.long_name = 'Mask'
        Mask.standard_name = 'Mask'
        Mask.units = '-'
        Mask.scale_factor = 1

    # Import (and optionally resample) Glacier Mask
    Glacier_mask_file_name = os.path.join(file_data['static_data_path'], file_data['Glacier_mask_name'])
    Glacier_Mask_obj = get_file_raster(Glacier_mask_file_name)

    if file_data['sim_regrid_on_DEM']:
        Glacier_Mask_obj = regrid_raster(Glacier_Mask_obj, DEM_obj)

    # we round to the nearest integer to remove spurious results from resampling
    Glacier_Mask_obj['values'] = np.round(Glacier_Mask_obj['values'])
    # now we leverage Glacier_value_in_mask to create a binary glacier mask
    Glacier_Mask_obj['values'] = np.where(Glacier_Mask_obj['values'] == file_data['Glacier_value_in_mask'], 1, 0)
    # since we now removed the -9999 outside the simulation domain, we reset them
    Glacier_Mask_obj['values'] = np.where(DEM_obj['values'] == -9999, -9999, Glacier_Mask_obj['values'])

    # write
    GlacierMask = ds.createVariable("GlacierMask", "f", ("Y", "X",))

    # attributes thickness
    GlacierMask[:] = np.flipud(Glacier_Mask_obj['values'])
    GlacierMask.grid_mapping = ''
    GlacierMask.coordinates = ''
    GlacierMask.cell_method = ''
    GlacierMask.pressure_level = ''
    GlacierMask.long_name = 'GlacierMask'
    GlacierMask.standard_name = 'GlacierMask'
    GlacierMask.units = '-'
    GlacierMask.scale_factor = 1

    # Import (and optionally resample) glacier-debris coefficient
    if file_data['Glacier_debris']:
        Glacier_debris_file_name = os.path.join(file_data['static_data_path'], file_data['Glacier_debris_name'])
        Glacier_debris_obj = get_file_raster(Glacier_debris_file_name)

        if file_data['sim_regrid_on_DEM']:
            Glacier_debris_obj = regrid_raster(Glacier_debris_obj, DEM_obj)

        # write
        Glacier_debris = ds.createVariable("GlacierDebris", "f", ("Y", "X",))

        # attributes thickness
        Glacier_debris[:] = np.flipud(Glacier_debris_obj['values'])
        Glacier_debris.grid_mapping = ''
        Glacier_debris.coordinates = ''
        Glacier_debris.cell_method = ''
        Glacier_debris.pressure_level = ''
        Glacier_debris.long_name = 'Glacier_debris'
        Glacier_debris.standard_name = 'Glacier_debris'
        Glacier_debris.units = '-'
        Glacier_debris.scale_factor = 1

    #close NC file
    ds.close()
    os.system("gzip -f " + NetCDF_full_path)



# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="file_settings")
    parser_values = parser_handle.parse_args()

    if parser_values.file_settings:
        file_settings = parser_values.file_settings
    else:
        file_settings = 'configuration.json'

    return file_settings
# -------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
