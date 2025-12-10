import json
import datetime as dt
import pandas as pd
import numpy as np
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

SIMULATION_KEYS = ['lw_obj', 'model', 'start_position', 'start_t', 'end_t',
                  'num', 'rad', 'ship', 'wdf', 'orientation', 'seed_type',
                  'time_step', 'configurations', 'file_name', 'vocabulary']
DATASET_KEYS = ['start_t', 'end_t', 'border', 'folder', 'concatenation',  'copernicus', 'user', 'pword']
REQUIRED_KEYS = ['model','start_position', 'start_t', 'end_t']
VOC = ["Copernicus", "ECMWF", "Copernicus_edited"]
CHECK = True
# Help functions
def verify_border(border):
    if isinstance(border, list) and len(border) == 4:
        if border[0] < border[1] and border[2] < border[3]:
            return True
    return False

def unknown_keys(config: dict, sim_keys: list, ds_keys: list):
    allowed = set(sim_keys) | set(ds_keys)
    return list(set(config.keys()) - allowed)

# Model-specific check functions
def check_oceandrift(file, sim_vars):
    val = file.get('wdf')
    if val is not None and isinstance(val, float) and (0 <= val <= 1):
        sim_vars['wdf'] = val
    elif val is not None and isinstance(val, list) and len(val) == file.get('num'):
        sim_vars['wdf'] = val
        logging.info(f"Wind drift factor is given as a list: {val}. Number of elements must match length of wdf.")
    else:
        logging.warning(f"Invalid wind drift factor: {val}. Must be float in [0, 1]. Using default value 0.02")
    return sim_vars

def check_leeway(file, sim_vars):
    val = file.get('lw_obj')
    if val is not None and isinstance(val, int) and (0 < val <= 85):
        sim_vars['lw_obj'] = val
    else:
        logging.warning(f"Invalid leeway object: {val}. Must be integer in [1, 85]. Using default value 1")
    return sim_vars

def check_shipdrift(file, sim_vars):
    ship = file.get('ship')
    orientation = file.get('orientation')
    if ship is not None and isinstance(ship, list) and len(ship) == 4:
        sim_vars['ship'] = ship
    else:
        logging.warning(f"Invalid ship parameters: {ship}. Must be list of four numeric values. Using default values [length, beam, height, draft]. Using default value [62, 8, 10, 5].")
    if orientation is not None and isinstance(orientation, list) and orientation in ['left', 'right', 'random']:
        sim_vars['orientation'] = orientation
    else:
        logging.warning(f"Invalid orientation parameters: {orientation}. Must be one of [left, right, random]. Using default value random.")
    return sim_vars


# Simulation settings check functions
# Seed settings. If missing or invalid, use default values from function definition. 
# Not crashing, just warning. 
def check_seed_settings(file, sim_vars):
    rules = {
        "seed_type": {
            "valid": lambda v: v in ["elements", "cone"],
            "error": "Invalid or missing seed_type: {}. Using default: elements",
        },
        "num": {
            "valid": lambda v: isinstance(v, int) and v > 0,
            "error": "Invalid or missing num: {}. Must be positive integer. Using default: 100",
        },
        "rad": {
            "valid": lambda v: isinstance(v, int) and v >= 0,
            "error": "Invalid or missing rad: {}. Must be positive integer. Using default: 0",
        }
    }

    for key, rule in rules.items():
        val = file.get(key)
        if val is not None and rule["valid"](val):
            sim_vars[key] = val
        else:
            logging.warning(rule["error"].format(val))

    logging.info("Seed settings verified, success!")
    return sim_vars

# Time settings. If missing or invalid, use default values from function definition.
# Return error if: incorect start time or end time. 
# If time step is incorrect or not given, use default.
def check_time_settings(file, sim_vars, data_vars):
    flag = True
    times = {}
    for key in ["start_t", "end_t"]:
        val = file.get(key)
        try:
            times[key] = pd.to_datetime(val)
            sim_vars[key] = val
            data_vars[key] = val
        except Exception:
            flag = False
            logging.error(f"Invalid or missing {key}: {val}. Must be a valid datetime string.")
            
    start = times.get("start_t")
    end = times.get("end_t")
    if start is not None and end is not None:
        if start >= end:
            flag = False
            logging.error(f"Start time: {start} must be earlier than end time: {end}.")   
                 
    time_step = file.get("time_step")
    
    if isinstance(time_step, int) and time_step > 0:
        sim_vars['time_step'] = time_step
    else:
        logging.warning(f"Invalid or missing time_step: {time_step}. Must be a positive integer.")
        
    if flag:
        logging.info("Time settings verified, success!")
    return flag, sim_vars, data_vars

# Position settings. Will drop off if invalid position. Accept them if everythin is ok.
def check_position_settings(file, sim_vars):
    flag = True
    rules = [
        {
            "valid": lambda arr: arr.ndim <= 2 and arr.shape[0] == 2,
            "error": 'Inapropriate array dimension size of start position coordinates.',
        },
        {
            "valid": lambda arr: arr[0].size == arr[1].size,
            "error": "start_position must contain [latitudes, longitudes].",
        },
        {
            "valid": lambda arr: np.all((-90 <= arr[0]) & (arr[0] <= 90)),
            "error": "Latitude values must be in [-90, 90].",
        },
        {
            "valid": lambda arr: np.all((-180 <= arr[1]) & (arr[1] <= 180)),
            "error": "Longitude values must be in [-180, 180].",
        },  
    ]
    val = file.get('start_position')
    
    if val is None:
        logging.error("Missing start_position.")
        return False, sim_vars
    
    if not isinstance(val, list) or len(val) != 2:
        logging.error(f"start_position must be a list of two arrays/lists. Got: {val}")
        return False, sim_vars
    
    try:
        arr = np.asarray(val, dtype=float)
    except Exception:
        logging.error(f"start_position contains non-numeric values: {val}")
        return False, sim_vars
    
    for rule in rules:
        try:
            if not rule["valid"](arr):
                logging.error(rule["error"])
                flag = False
        except Exception:
            logging.error(f"Error while validating: {rule['error']}")
            flag = False
            
    if flag:
        sim_vars.update({'start_position': file['start_position']})
        logging.info('Position settings verified, success!')
    return flag, sim_vars


def check_data_settings(file, data_vars):
    rules = {
        "border": {
            "valid": lambda v: verify_border(v),
            "error": "Invalid or missing border: {}. Using default: [13, 30, 54, 62]",
        },
        "folder": {
            "valid": lambda v: isinstance(v, str) and os.path.isdir(v),
            "error": "Invalid or missing folder: {}. Must be valid path.",
        },
        "concatenation": {
            "valid": lambda v: isinstance(v, bool),
            "error": "Invalid or missing concatenation: {}. Must be True or False. Using default: False",
        },
        "copernicus": {
            "valid": lambda v: isinstance(v, bool) ,
            "error": "Invalid or missing copernicus: {}. Must be True or False. Using default: False",
        }
    }
    additional_rules = {
        "user": {
            "valid": lambda v: isinstance(v, str) and len(v) > 0,
            "error": "Invalid or missing user: {}. Must be non-empty string.",
        },
        "pword": {
            "valid": lambda v: isinstance(v, str) and len(v) > 0,
            "error": "Invalid or missing pword: {}. Must be non-empty string.",
        },
    }

    for key, rule in rules.items():
        val = file.get(key)
        if val is not None and rule["valid"](val):
            data_vars[key] = val
        else:
            logging.warning(rule["error"].format(val))
            
    if data_vars.get("copernicus", False):
        for key, rule in additional_rules.items():
            val = file.get(key)
            if val is not None and rule["valid"](val):
                data_vars[key] = val
            else:
                logging.error(rule["error"].format(val))

    logging.info("Data settings verified, success!")
    return data_vars


def verify_config_file(file_path):
    sim_vars = dict()
    data_vars = dict()
    flag = True
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
    except:
        logging.error('Unable to read or parse the configuration file.')
        return False, sim_vars, data_vars
    
    if all(key in config.keys() for key in REQUIRED_KEYS):
        # logging.info('File reading successful. Main keys found:', list(config.keys()))
        sim_vars['model'] = config['model']
        flag, sim_vars = check_position_settings(config, sim_vars)
        flag, sim_vars, data_vars = check_time_settings(config, sim_vars, data_vars)
        sim_vars  = check_seed_settings(config, sim_vars)
        data_vars = check_data_settings(config, data_vars)
        match config['model']:
            case 'OceanDrift':
                sim_vars = check_oceandrift(config, sim_vars)
            case 'Leeway':
                sim_vars = check_leeway(config, sim_vars)
            case 'ShipDrift':
                sim_vars = check_shipdrift(config, sim_vars)
            case _:
                logging.error(f"Unknown model type: {config['model']}")
                flag = False
                
        name = config.get('file_name')
        if name is not None:
            sim_vars['file_name'] = name
            
        cnf = config.get('configurations')
        if cnf is not None:
            if isinstance(cnf, dict):
                sim_vars['configurations'] = cnf
            else:
                logging.warning(f"Invalid configurations: {cnf}. Must be a dictionary. Skipping configurations.")
            
        vc = config.get('vocabulary')
        if vc is not None:
            if vc in VOC:
                sim_vars['vocabulary'] = vc
            else:
                logging.error(f"Unknown variable mapping vocabulary: {vc}")
                flag = False
        
        
    else:
        logging.error('Missing required keys in the configuration file.')
            
    residuals = unknown_keys(config, SIMULATION_KEYS, DATASET_KEYS)    
    if len(residuals)>0:
        logging.warning(f"Unknown keys in configuration file: {residuals}")
        
    logging.info("Configuration verification completed.")    
    logging.info(f"Configurations used for data preparation: \n {json.dumps(data_vars, indent=2)}")
    logging.info(f"Configurations used for simulation: \n {json.dumps(sim_vars, indent=2)}")

    return flag, sim_vars, data_vars