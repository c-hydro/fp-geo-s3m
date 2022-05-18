#!/bin/bash -e
virtualenv_folder='/home/fp_virtualenv_python3/'
virtualenv_name='fp_virtualenv_python3_hyde_libraries'
script_file='/home/S3M_StaticDataprep.py'
settings_file='/home/S3M_StaticDataprep_configuration.json'

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"

#-----------------------------------------------------------------------------------------
# Run python script (using setting and time)
python3 $script_file -settings_file $settings_file
