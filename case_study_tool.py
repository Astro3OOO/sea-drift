import xarray as xr
import opendrift
from opendrift.readers import reader_netCDF_CF_generic
from opendrift.models.oceandrift import OceanDrift
from opendrift.models.leeway import Leeway
from opendrift.models.shipdrift import ShipDrift
import datetime as dt
import zoneinfo
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import copernicusmarine
from opendrift.readers.reader_netCDF_CF_generic import Reader
import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )
logger_od = logging.getLogger('opendrift') 
logger_od.setLevel(logging.CRITICAL)

logger_cop = logging.getLogger('copernicusmarine') 
logger_cop.setLevel(logging.WARNING)


def get_time_from_reader(agg, lst, type):
    if type == 'start':
        if type(lst) == list:
            new_lst = []
            for element in lst:
                if type(element.start_time) == dt.datetime or type(element) == pd._libs.tslibs.timestamps.Timestamp:
                    new_lst.append(element.start_time)
            if agg == 'Max':
                return max(new_lst)
            elif agg == 'Min':
                return min(new_lst)
            else:
                logging.warning(f'Aggregation {agg} is not supported')
        else:
            return lst.start_time
    elif type == 'end':
        if type(lst) == list:
            new_lst = []
            for element in lst:
                if type(element.end_time) == dt.datetime or type(element) == pd._libs.tslibs.timestamps.Timestamp:
                    new_lst.append(element.end_time)
            if agg == 'Max':
                return max(new_lst)
            elif agg == 'Min':
                return min(new_lst)
            else:
                logging.warning(f'Aggregation {agg} is not supported')
        else:
            return lst.end_time
    else:
        logging.warning(f'Type {type} is unsupported')
        return

def PrepareStartTime(start_t, reader = None):
    if isinstance(start_t, dt.datetime):
        return start_t
    elif isinstance(start_t, pd._libs.tslibs.timestamps.Timestamp):
        return start_t
    elif isinstance(start_t, int) or isinstance(start_t, str):
        try:
            start = pd.to_datetime(start_t)
            return start
        except:
            logging.warning(f'Unable to transform {start_t} start time into pandas Timesamp.')
            start_t = None
    elif start_t is None and reader is not None:
        return get_time_from_reader('Min', reader, 'start')
    else:
        logging.error(f'Incorrect start time input {start_t}. Returning placeholder')
        return dt.datetime.now()
    
def PrepareEndTime(end_t, reader = None):
    if isinstance(end_t, dt.datetime):
        return end_t
    elif isinstance(end_t, pd._libs.tslibs.timestamps.Timestamp):
        return end_t
    elif isinstance(end_t, int) or isinstance(end_t, str):
        try:
            end = pd.to_datetime(end_t)
            return end
        except:
            logging.warning(f'Unable to transform {end_t} start time into pandas Timesamp.')
            end_t = None
    elif end_t is None and reader is not None:
        return get_time_from_reader('Max', reader, 'end')
    else:
        logging.error(f'Incorrect end time input {end_t}. Returning placeholder')
        return dt.datetime.now() + dt.timedelta(day = 2)

def PrepareDataSet(start_t, end_t, border = [54, 62, 13, 30],
                   folder = None, concatenation =False, copernicus = False,
                   user = None, pword = None):
    wind = False
    # Lists of datasets that will be used in Reader.
    # List may consist of singe datstets (eg atmoshperic model, wind model) 
    # or combined datasets (atmo combined, wind combined)
    ds_ecmwf = []
    ds_netcdf = []
    ds_copernicus = []
    ds_wind = []
    
    start_t = PrepareStartTime(start_t)
    end_t = PrepareEndTime(end_t)
    
    if folder != None:
        if concatenation:
            for subdir in os.listdir(folder):
                buffer_ecmwf = []
                buffer_netcdf = []
                buffer_wind = []
                full_path = os.path.join(folder, subdir)
                if os.path.isdir(full_path):
                    for file in os.listdir(full_path):
                        if file.endswith('.grib'):
                            ds = xr.open_dataset(os.path.join(folder,subdir,file), engine='cfgrib')
                            ds = ds.assign_coords(time=ds['time'] + ds['step'])
                            ds = ds.swap_dims({'step': 'time'})
                            buffer_ecmwf.append(ds)
                            ds.close()
                            if 'u10' in ds.data_vars:
                                buffer_wind.append(xr.Dataset({'u10' : ds['u10'],
                                                    'v10': ds['v10']}))
                                wind = True
                        if file.endswith('.nc'):
                            ds = xr.open_dataset(os.path.join(folder,subdir,file), engine='netcdf4')    
                            buffer_netcdf.append(ds)
                            ds.close()

                            
                    buffers = {'ecmwf': buffer_ecmwf, 'netcdf': buffer_netcdf, 'wind': buffer_wind}
                    targets = {'ecmwf': ds_ecmwf, 'netcdf': ds_netcdf, 'wind': ds_wind}

                    for key in ['ecmwf','netcdf','wind']:
                        buf = buffers[key]
                        if buf:
                            merged = xr.concat(buf, dim='time')
                            merged = merged.sortby('time')
                            merged = merged.drop_duplicates(dim='time')
                            targets[key].append(merged) 
                else:
                    logging.error(f'{full_path} Is not a valid directory.')

        
        else:
            for file in os.listdir(folder):
                if file.endswith('.grib'):
                    ds = xr.open_dataset(os.path.join(folder,file), engine='cfgrib')
                    ds = ds.assign_coords(time=ds['time'] + ds['step'])
                    ds = ds.swap_dims({'step': 'time'})
                    ds_ecmwf.append(ds)
                    ds.close()

                    if 'u10' in ds.data_vars:
                        ds_wind = xr.Dataset({'u10' : ds['u10'],
                                            'v10': ds['v10']})
                        wind = True
                if file.endswith('.nc'):
                    ds = xr.open_dataset(os.path.join(folder,file), engine='netcdf4')    
                    ds_netcdf.append(ds)
                    ds.close()

    else:
        logging.error('Add folder with ECMWF datasets.')
            
    if copernicus:
        if user is None or pword is None:
            logging.error('No login credentials provided.')
            return []
        if border is None:
            logging.error('No border provided. Cropped area must be added!')
            return []
        try:
            ds_1 = copernicusmarine.open_dataset(dataset_id='cmems_mod_bal_phy_anfc_PT1H-i', chunk_size_limit=0,
                                                username=user, password = pword,
                                                minimum_latitude=border[0], maximum_latitude=border[1],
                                                minimum_longitude=border[2], maximum_longitude=border[3],
                                                minimum_depth=0.5016462206840515, maximum_depth=0.5016462206840515,
                                                start_datetime=start_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')),
                                                end_datetime=end_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')))
            ds_copernicus.append(ds_1)
            ds_1.close()
            
            ds_2 = copernicusmarine.open_dataset(dataset_id='cmems_mod_bal_wav_anfc_PT1H-i', chunk_size_limit=0,
                                                username = user,  password = pword,
                                                minimum_latitude=border[0], maximum_latitude=border[1],
                                                minimum_longitude=border[2], maximum_longitude=border[3],
                                                start_datetime=start_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')),
                                                end_datetime=end_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')))
            ds_copernicus.append(ds_2)
            ds_2.close()
            
        except:
            logging.warning('No data found in Copernicus Baltic. Searching in copernicus global...')
            # ds_copernicus = []
            try:
                ds_1 = copernicusmarine.open_dataset(dataset_id='cmems_mod_glo_phy_anfc_0.083deg_PT1H-m', chunk_size_limit=0,
                                                    username=user, password = pword, 
                                                    minimum_latitude=border[0], maximum_latitude=border[1],
                                                    minimum_longitude=border[2], maximum_longitude=border[3],
                                                    minimum_depth=0.49402499198913574, maximum_depth=0.49402499198913574,
                                                    start_datetime=start_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')),
                                                    end_datetime=end_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')))
                ds_copernicus.append(ds_1)
                ds_1.close()

                ds_2 = copernicusmarine.open_dataset(dataset_id='cmems_mod_glo_wav_anfc_0.083deg_PT3H-i', chunk_size_limit=0, 
                                                    username=user, password = pword,
                                                    minimum_latitude=border[0], maximum_latitude=border[1],
                                                    minimum_longitude=border[2], maximum_longitude=border[3],
                                                    start_datetime=start_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')),
                                                    end_datetime=end_t.replace(tzinfo=zoneinfo.ZoneInfo('UTC')))
                ds_copernicus.append(ds_2)
                ds_2.close()

            except:
                logging.warning('No requested data in Copernicus Global.')
        ds_3 = copernicusmarine.open_dataset(dataset_id='cmems_mod_bal_wav_anfc_static', chunk_size_limit=0,
                                            username = user, password = pword,
                                            minimum_latitude=border[0], maximum_latitude=border[1],
                                            minimum_longitude=border[2], maximum_longitude=border[3])
        ds_copernicus.append(ds_3)
        ds_3.close()

                
    if wind:
        if len(ds_netcdf)>0:
            ds_netcdf.append(ds_wind)
        if len(ds_copernicus)>0:
            ds_copernicus.append(ds_wind)
    
    if folder != None and copernicus:
        if len(ds_netcdf)>0 and len(ds_ecmwf)>0 and len(ds_copernicus)>0:
            logging.info('Returning 3 datasets : [folder.grib, folder.nc, copernicus]')
            return [ds_ecmwf, ds_netcdf, ds_copernicus]
        elif len(ds_netcdf)>0 and len(ds_copernicus)>0:
            logging.info('Returning 2 datasets : [folder.nc, copernicus]')
            return [ds_netcdf, ds_copernicus]
        elif len(ds_ecmwf)>0 and len(ds_copernicus)>0:
            logging.info('Returning 2 datasets : [folder.grib, copernicus]')
            return [ds_ecmwf, ds_copernicus]
        elif len(ds_copernicus)>0:
            logging.info('Returnng only Copernicus dataset, as the other one is empty.')
        else:
            logging.error(' Folder data and copernicus data flags were enabled but no dataset was provided. Returning empty list.')
            return []
    elif folder != None:
        if len(ds_netcdf)>0 and len(ds_ecmwf)>0:
            logging.info('Returning 2 datasets : [folder.grib, folder.nc]')
            return [ds_ecmwf, ds_netcdf]
        elif len(ds_netcdf)>0:
            logging.info('Returning 1 datasets : [folder.nc]')
            return ds_netcdf
        elif len(ds_ecmwf)>0:
            logging.info('Returning 1 datasets : [folder.grib]')
            return ds_ecmwf
        else:
            logging.error('Folder data flag was enabled but no dataset was provided. Returning empty list.')
            return []
    elif copernicus:
        if len(ds_copernicus)>0:
            logging.info('Returning 1 datasets : [copernicus]')
            return ds_copernicus
        else:
            logging.error(' Copernicus flag was enabled but no dataset was provided. Returning empty list.')
            return []
    else:
        logging.error('No dataset to return.')
        return []                  

def seed(o, model, lw_obj, start_position, start_t, num, rad, ship, wdf, seed_type, orientation):
    
    if model == OceanDrift:
        if seed_type == 'elements':
            o.seed_elements(lat = start_position[0], lon = start_position[1], number = num, radius=rad, wind_drift_factor = wdf, time = start_t)
        elif seed_type == 'cone':
            o.seed_cone(lat = start_position[0], lon = start_position[1], number = num, radius=rad, wind_drift_factor = wdf, time = start_t)
        else:
            logging.error('Unsupported seed type')
        return o
    
    if model == Leeway:
        if seed_type == 'elements':
            o.seed_elements(lat = start_position[0], lon = start_position[1], number = num, radius=rad, object_type = lw_obj, time = start_t)
        elif seed_type == 'cone':
            o.seed_cone(lat = start_position[0], lon = start_position[1], number = num, radius=rad, object_type = lw_obj, time = start_t)
        else:
            logging.error('Unsupported seed type')
        return o
    
    if model == ShipDrift:
        length, beam, height, draft = ship
        o.set_config('seed:orientation', orientation)
        if seed_type == 'elements':
            o.seed_elements(lat = start_position[0], lon = start_position[1], number = num,
                            length = length, beam = beam, height = height, draft = draft, radius=rad, time = start_t)
        elif seed_type == 'cone':
            o.seed_cone(lat = start_position[0], lon = start_position[1], number = num, radius=rad,   
                        length = length, beam = beam, height = height, draft = draft, time = start_t)
        else:
            logging.error('Unsupported seed type')
        return o
    
    logging.error(f'Model {model} is not implemented yet.')
    
    return o

model_dict = {'OceanDrift':OceanDrift,
              'Leeway':Leeway,
              'ShipDrift':ShipDrift}

def simulation(lw_obj=1, model='OceanDrift', start_position=None, start_t=None,
               end_t=None, datasets=None, std_names=None, num=100,
               rad=0, ship=[62, 8, 10, 5], wdf=0.02, orientation = 'random',
               delay=False, multi_rad=False, seed_type=None, time_step = None,
               configurations = None, file_name = None, vocabulary = None):
    '''
    model : choose or add apropriate OpenDrift model for your simulation.
    start_position : enter start position [latitude, longitude]. It can be [float, float] or [list, list].
    start_t : start time for seed and simulation. If not provided, readers start time is used. 
    end_t : end time for simulation. If not provided simulation continue to the readers end time.
    datesets : xarray.dataset or list of xarray.datasets. 
    std_names : dict :  standard name mapping, different for ecmwf and copernicus. 
    num : number of elements per seed.
    rad : numeric or list. Numeric for radial seed, list for cone seed. 
    ship : [length, beam, height, draft]
    wdf : wind drift factor, default 2% for OceanDrift
    lw_obj : leeway object from list 
    '''
    
    # Check main requirments
    if start_position == None:
        logging.error('Start position is required')
        return
    if datasets == None:
        logging.error('At least one dataset is required')
        return
    if seed_type == None:
        seed_type = 'elements'
    if model not in model_dict.keys():
        logging.error(f'Model {model} is not supported. Choose one of the following: {list(model_dict.keys())}')
        return
    model = model_dict[model]   
    
    
    # Create readers
    if type(datasets) == list:
        reader = [Reader(ds, standard_name_mapping=std_names) for ds in datasets]
    else:
        reader = Reader(datasets, standard_name_mapping=std_names)
        
    # Prepare start and end times
    start_t = PrepareStartTime(start_t, reader)
    end_t = PrepareEndTime(end_t, reader)
    
    if file_name == None:
        m = str(model).split('.')[-1][:-2]
        t_now = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        t_strt = start_t.strftime("%Y-%m-%d_%H%M")
        file_name = f'{m}_{t_strt}_{t_now}.nc'
    
    output_dir = "/OUTPUT"  
    os.makedirs(output_dir, exist_ok=True)    
    file_name = os.path.join(output_dir, file_name)
    # Create a model and add readers
    o = model(loglevel = 50)
    if configurations is not None:
        for key, value in configurations.items():
            o.set_config(key, value)
    o.add_reader(reader)
    # Seed

    o = seed(o=o, model=model, lw_obj=lw_obj, num = num, rad = rad, start_t = start_t, 
             start_position=start_position, ship=ship, wdf = wdf, seed_type=seed_type, orientation=orientation)
    # Run
    if time_step is None:
        o.run(end_time=end_t, outfile = file_name)
    else:
        o.run(end_time=end_t, time_step=time_step, time_step_output=time_step, outfile = file_name)
            
    return o
