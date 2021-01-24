
'''
#* this file is setting of environemnt values
load the .env file and save to dotenv_path
'''

import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
