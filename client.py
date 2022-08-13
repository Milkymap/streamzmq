import zmq 
import cv2 
import click 

import pickle

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

from libraries.log import logger 

@click.command()
@click.option('--router_address', type=str, help='address of the remote router')
@click.option('--publisher_address', type=str, help='address of the publisher')
def grabber(router_address, publisher_address):
    ZMQ_INIT = 0
    try:
        ctx = zmq.Context()
        dealer_socket = ctx.socket(zmq.DEALER)
        dealer_socket.setsockopt(zmq.LINGER, 0)
        dealer_socket.connect(router_address)

        dealer_socket_poller = zmq.Poller()
        dealer_socket_poller.register(dealer_socket, zmq.POLLIN)
        ZMQ_INIT = 1  # dealer was initialized 

        dealer_socket.send_multipart([b'', b'join'])
        logger.debug('client try to connect to remote server')
        incoming_events = dict(dealer_socket_poller.poll(5000))  # wait 5s for server to reply 
        dealer_socket_status = incoming_events.get(dealer_socket, None)
        if dealer_socket_status is not None: 
            if dealer_socket_status == zmq.POLLIN: 
                _, message = dealer_socket.recv_multipart()
                if message == b'accp': 
                    logger.success('the connection was established')
                    subscriber_socket = ctx.socket(zmq.SUB)
                    subscriber_socket.setsockopt(zmq.LINGER, 0)
                    subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'step')
                    subscriber_socket.setsockopt(zmq.SUBSCRIBE, b'exit')
                    subscriber_socket.connect(publisher_address)
                    ZMQ_INIT = 2  # dealer and subscriber were initialized 
                    
                    subtractor = cv2.createBackgroundSubtractorKNN()
                    keep_grabbing = True 
                    while keep_grabbing:
                        key_code = cv2.waitKey(25) & 0xFF 
                        if key_code == 27:
                            keep_grabbing = False 
                        topic, encoded_data = subscriber_socket.recv_multipart()
                        print(topic)
                        if topic == b'step': 
                            bgr_image = pickle.loads(encoded_data)
                            segmentation_mask = subtractor.apply(bgr_image)
                            contours, _ = cv2.findContours(segmentation_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                            for cnt in contours: 
                                x, y, w, h = cv2.boundingRect(cnt)
                                cv2.rectangle(bgr_image, (x, y), (x + w, y + h), 0, 3)
                            print(bgr_image)
                            cv2.imshow('001', cv2.resize(bgr_image, (600, 600)))
                        if topic == b'exit':
                            logger.debug('server has exit the connection')
                            keep_grabbing = False 
                    # end loop grabbing 
                else:
                    logger.warning('connection was refused')
        else:
            logger.debug('server was not able to respond in time')
    except KeyboardInterrupt:
        pass 
    except Exception as e:
        logger.error(e)
    finally: 
        if ZMQ_INIT == 2:
            subscriber_socket.close()
        if ZMQ_INIT >= 1:
            dealer_socket_poller.unregister(dealer_socket)
            dealer_socket.close()
            ctx.term()

if __name__ == '__main__':
    grabber()