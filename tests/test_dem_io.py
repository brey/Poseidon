import pyposeidon.dem as pdem
import pyposeidon.model as pmodel
import pyposeidon.grid as pgrid


import pytest
import xarray as xr
import os
import shutil
import numpy as np


from . import DATA_DIR

DEM_SOURCE = DATA_DIR / "dem.nc"

#define the lat/lon window and time frame of interest
window1 = {
    'lon_min' : -30,
    'lon_max' : -10.,
    'lat_min' : 60.,
    'lat_max' : 70.,
    'dem_source' : DEM_SOURCE,
}



def schism(tmpdir,kwargs):

    grid = pgrid.grid(type='tri2d',grid_file=(DATA_DIR / 'hgrid.gr3').as_posix())

    #update dem

    xp = grid.Dataset.SCHISM_hgrid_node_x.values
    yp = grid.Dataset.SCHISM_hgrid_node_y.values

    kwargs.update({'grid_x':xp, 'grid_y':yp})
    #get dem
    df = pdem.dem(**kwargs)

    grid.Dataset['depth'].loc[:] = -df.Dataset.ival.values

    filename_ = str(tmpdir.join('hgrid_.gr3'))
    #output to grid file
    grid.to_file(filename_)

    #read again new grid
    grid_ = pgrid.grid(type='tri2d',grid_file=filename_)

    #compare
    return grid.Dataset.equals(grid_.Dataset)

def d3d(tmpdir, kwargs):

    ## lat,lon grid
    resolution=.1
    lon=np.arange(kwargs['lon_min'],kwargs['lon_max'],resolution)
    lat=np.arange(kwargs['lat_min'],kwargs['lat_max'],resolution)
    xp, yp = np.meshgrid(lon,lat)

    kwargs.update({'grid_x':xp, 'grid_y':yp})

    #get dem
    df = pdem.dem(**kwargs)

    rpath = str(tmpdir)+'/'
    #output
    pdem.to_output(df.Dataset,solver='d3d',rpath=rpath)

    #read again dem
    m = pmodel(solver='d3d')
    rd = m.from_dep(rpath + 'd3d.dep')

    #compare
    c1 = -rd.where(rd!=-999)
    c2 = df.Dataset.ival.where(df.Dataset.ival < 0)

    return c1.fillna(0).equals(c2.fillna(0))



@pytest.mark.parametrize('kwargs', [ window1 ])
@pytest.mark.parametrize('solver', [schism, d3d])
def test_answer(tmpdir, kwargs, solver):
    assert solver(tmpdir,kwargs) == True

