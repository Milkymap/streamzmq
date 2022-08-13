import zmq 
import cv2 
import click 

import pickle

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

from libraries.log import logger 

@click.command()
@click.option('--publisher_address', type=str, help='address of the publisher')
def grabber(publisher_address):
    ZMQ_INIT = 0
    try:
        ctx = zmq.Context()

        logger.success('the connection was established')
        subscriber_socket = ctx.socket(zmq.SUB)
        subscriber_socket.setsockopt(zmq.LINGER, 0)
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'step')
        subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'exit')
        subscriber_socket.connect(publisher_address)
        ZMQ_INIT = 1  # dealer and subscriber were initialized 
        
        keep_grabbing = True 
        while keep_grabbing:
            key_code = cv2.waitKey(25) & 0xFF 
            if key_code == 27:
                keep_grabbing = False 
            topic, encoded_data = subscriber_socket.recv_multipart()
            print(topic)
            if topic == b'step': 
                decoded_data = pickle.loads(encoded_data)
                print(decoded_data)
                bgr_image = cv2.imdecode(decoded_data, cv2.IMREAD_GRAYSCALE)
                cv2.imshow('001', cv2.resize(bgr_image, (600, 600)))
                # haskell .... is great
            if topic == b'exit':
                logger.debug('server has exit the connection')
                keep_grabbing = False 
        # end loop grabbing 
    except KeyboardInterrupt:
        pass 
    except Exception as e:
        logger.error(e)
    finally: 
        if ZMQ_INIT == 1:
            subscriber_socket.close()
            ctx.term()

if __name__ == '__main__':
    grabber()