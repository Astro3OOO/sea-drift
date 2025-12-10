from config_verification import verify_config_file
from case_study_tool import simulation, PrepareDataSet
import sys
import json 
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    input_file = sys.argv[1]

    logging.info("Validating input...")
    
    path = 'INPUT'
    input_file = os.path.join(path, input_file)

    is_valid, sim_vars, data_vars = verify_config_file(input_file)

    if not is_valid:
        logging.error("Validation failed. Exiting.")
        return
    with open("DATA/VariableMapping.json", 'r') as f:
        vacabulary = json.load(f)
    
    logging.info("Input valid. Preparing datasets...")
    ds = PrepareDataSet(**data_vars)
    
    logging.info("Dataset ready. Running simulation...")
    vc = sim_vars['vocabulary']
    simulation(datasets=ds, std_names=vacabulary[vc], **sim_vars)

    print("Simulation completed successfully.")
    
    with open('/OUTPUT/used_packages.txt', 'w') as file:
        file.write("\n".join(sorted(sys.modules.keys())))
if __name__ == "__main__":
    main()