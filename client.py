import zmq 
import cv2 
import click 

import pickle

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

import time 

from libraries.log import logger 

@click.command()
@click.option('--path2video')
@click.option('--router_address', type=str, help='address of the remote router')
def grabber(path2video, router_address):
    ZMQ_INIT = 0
    try:
        ctx = zmq.Context()
        
        dealer_socket = ctx.socket(zmq.DEALER)
        dealer_socket.setsockopt(zmq.LINGER, 0)
        dealer_socket.connect(router_address)

        dealer_socket_poller = zmq.Poller()
        dealer_socket_poller.register(dealer_socket, zmq.POLLIN)
        ZMQ_INIT = 1  # dealer was initialized 

        dealer_socket.send_multipart([b'', b'join', b''])
        logger.debug('client try to connect to remote server')
        incoming_events = dict(dealer_socket_poller.poll(5000))  # wait 5s for server to reply 
        dealer_socket_status = incoming_events.get(dealer_socket, None)
        
        if dealer_socket_status is not None: 
            if dealer_socket_status == zmq.POLLIN: 
                _, respond_type, _ = dealer_socket.recv_multipart()
                if respond_type == b'accp':
                    logger.success('server has accept the conenction')
                    video_reader = cv2.VideoCapture(path2video)
                    start = time.time()
                    keep_sending = True 
                    while keep_sending:
                        key_code = cv2.waitKey(25) & 0xFF 
                        capture_status, bgr_frame = video_reader.read()
                        keep_sending = key_code != 27 and capture_status
                        if keep_sending:
                            end = time.time()
                            duration = end - start 
                            if duration > 3:  # or motion detection ...! 
                                resized_bgr_frame = cv2.resize(bgr_frame, (256, 256))
                                dealer_socket.send_multipart([b'', b'data'], flags=zmq.SNDMORE)
                                dealer_socket.send_pyobj(resized_bgr_frame)
                                start = end 
                            cv2.imshow('000', bgr_frame)
                    # end loop sending ...! 
            else:
                logger.warning('connection was refused')
        else:
            logger.debug('server was not able to respond in time')

    except KeyboardInterrupt:
        pass 
    except Exception as e:
        logger.error(e)
    finally: 
        if ZMQ_INIT == 1:
            dealer_socket.send_multipart([b'', b'exit', b''])
            dealer_socket_poller.unregister(dealer_socket)
            dealer_socket.close()
            ctx.term()
            logger.debug('client has remvoed all ressources')

if __name__ == '__main__':
    grabber()