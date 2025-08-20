import yaml
import numpy as np

class PlateConfig:
	def __init__(self, config_fname):
		
		with open(config_fname, "r") as f:
			config = yaml.safe_load(f)
			for key, value in config.items():
				setattr(self, key, value)
		print(f"Successfully loaded {config_fname}")
	
	
	def get_unique_patient_ids(self):
		return list(np.unique(list(self.row_to_patient.values())))

	def set_plate_data(self, data_df):
		self.stat_df = data_df
  
	def calc_log_fold_changes


	