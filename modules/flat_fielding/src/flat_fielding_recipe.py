flat_recipe = """# recipe for flat fielding
from modules.utils.frame_combine import FrameCombinePrimitive
from modules.flat_fielding.src.flat_fielding import FlatFielding 

flat_files=find_files('input location')
master_flat_data=FrameCombinePrimitive(flat_files, 'NEID')
master_bias=find_files('input location')
master_result_data=master_flat_data-master_bias
master_result=to_fits(master_result_data, 'output location')

raw_file=find_files('input location')
raw_min_flat=FlatFielding(raw_file, master_result_data, 'NEID')
raw_min_flat=to_fits(raw_min_flat, 'output location')
"""
