import zmq 
import cv2 

import click 
import pickle 

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

from libraries.log import logger 

@click.command()
@click.option('--path2video')
@click.option('--router_port', type=int)
@click.option('--publisher_port', type=int)
def serving(path2video, router_port, publisher_port):
    ZMQ_INIT = 0 
    try:
        ctx = zmq.Context()
        router_socket = ctx.socket(zmq.ROUTER)
        router_socket.setsockopt(zmq.LINGER, 0)
        router_socket.bind(f'tcp://*:{router_port}')

        router_socket_poller = zmq.Poller()
        router_socket_poller.register(router_socket, zmq.POLLIN)

        publisher_socket = ctx.socket(zmq.PUB)
        publisher_socket.setsockopt(zmq.LINGER, 0)
        publisher_socket.bind(f'tcp://*:{publisher_port}')
        ZMQ_INIT = 1
        logger.success('server was initialized')

        video_reader = cv2.VideoCapture(path2video)
        keep_serving = True 
        while keep_serving:
            incoming_events = dict(router_socket_poller.poll(10))  # 10ms to check if there is an incoming connection
            router_socket_status = incoming_events.get(router_socket, None)
            if router_socket_status is not None: 
                if router_socket_status == zmq.POLLIN: 
                    client_id, _, message = router_socket.recv_multipart()
                    if message == b'join':
                        logger.debug('a new client attempt to join the server')
                        router_socket.send_multipart([client_id, b'', b'accp'])
            # end incoming events ... 
            key_code = cv2.waitKey(25) & 0xFF 
            capture_status, bgr_image = video_reader.read()
            keep_serving = key_code != 27 and capture_status
            gray_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
            resized_gray_image = cv2.resize(gray_image, (256, 256))
            publisher_socket.send_multipart([b'step'], flags=zmq.SNDMORE)
            publisher_socket.send_pyobj(resized_gray_image)
            cv2.imshow('000', cv2.resize(bgr_image, (600, 600)))
        # end loop serving ...! 
    except KeyboardInterrupt:
        pass 
    except Exception as e:
        logger.error(e)
    finally:
        if ZMQ_INIT == 1:
            publisher_socket.send_multipart([b'exit', b''])
            publisher_socket.close()
            router_socket_poller.unregister(router_socket)
            router_socket.close() 
            ctx.term()
            logger.success('server has removed all ressources')

if __name__ == '__main__':
    serving()