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

def main() -> int:
    if len(sys.argv) < 2:
        logging.error("Usage: python main.py <config.json>")
        return 1

    input_file = sys.argv[1]
    
    path = 'INPUT'
    input_file = os.path.join(path, input_file)
    if not os.path.exists(input_file):
        logging.error(f"Config file '{input_file}' does not exist.")
        return 2

    logging.info("Validating input...")
    is_valid, sim_vars, data_vars = verify_config_file(input_file)

    if not is_valid:
        logging.error("Validation failed.")
        return 3

    vocab_path = "DATA/VariableMapping.json"
    if not os.path.exists(vocab_path):
        logging.error(f"Vocabulary file missing: {vocab_path}")
        return 4

    try:
        with open(vocab_path, "r") as f:
            vocabulary_data = json.load(f)
    except json.JSONDecodeError:
        logging.error("Vocabulary JSON format error.")
        return 5

    logging.info("Input valid. Preparing datasets...")

    try:
        ds = PrepareDataSet(**data_vars)
    except Exception as e:
        logging.exception(f"Dataset preparation failed: {e}")
        return 6

    logging.info("Dataset ready. Running simulation...")

    vc = sim_vars.get("vocabulary")
    if vc not in vocabulary_data:
        logging.error(f"Requested vocabulary '{vc}' not found.")
        return 7

    try:
        simulation(datasets=ds, std_names=vocabulary_data[vc], **sim_vars)
    except Exception as e:
        logging.exception(f"Simulation failed: {e}")
        return 8

    print("Simulation completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())