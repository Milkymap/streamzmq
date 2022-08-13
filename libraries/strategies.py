import cv2 

import json 
import pickle

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

from os import path 
from PIL import Image 
from glob import glob
from time import time 
 
from libraries.log import logger 

map_serializers = {json: ('r', 'w'), pickle: ('rb', 'wb')}

def is_valid(var_value, var_name, var_type=None):
    if var_value is None:
        raise ValueError(f'{var_name} is not defined | please look the helper to see available env variables')
    if var_type is not None:
        if not op.attrgetter(var_type)(path)(var_value):
            raise ValueError(f'{var_name} should be a valid file or dir')

def measure(func):
    @ft.wraps(func)
    def _measure(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            duration = end_ if end_ > 0 else 0
            logger.debug(f"{func.__name__:<20} total execution time: {duration:04d} ms")
    return _measure

def read_image(path2image):
    cv_image = cv2.imread(path2image, cv2.IMREAD_COLOR)
    cv_image = cv2.resize(cv_image, (256, 256))
    return cv_image 

def pull_files(path2directory, extension='*'):
    all_paths = sorted(glob(path.join(path2directory, extension)))
    return all_paths 

def serialize(data, location, serializer):
    modes = map_serializers.get(serializer, None)
    if modes is None:
        raise Exception('serializer has to be [pickle or json]')
    with open(location, mode=modes[1]) as fp:
        serializer.dump(data, fp)
        logger.success(f'data was dumped at {location}')
    
def deserialize(location, serializer):
    modes = map_serializers.get(serializer, None)
    if modes is None:
        raise Exception('serializer has to be [pickle or json]')
    with open(location, mode=modes[0]) as fp:
        data = serializer.load(fp)
        logger.success(f'data was loaded from {location}')
    return data 



