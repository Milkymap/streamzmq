import zmq 
import cv2 

import click 
import pickle 

import numpy as np 
import operator as op 
import itertools as it, functools as ft 

from libraries.log import logger 

def create_window(win_name, win_size=(640, 480)):
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, *win_size)

@click.command()
@click.option('--router_port', type=int)
def serving(router_port):
    ZMQ_INIT = 0 
    try:
        ctx = zmq.Context()

        router_socket = ctx.socket(zmq.ROUTER)
        router_socket.setsockopt(zmq.LINGER, 0)
        router_socket.bind(f'tcp://*:{router_port}')
        
        router_socket_poller = zmq.Poller()
        router_socket_poller.register(router_socket, zmq.POLLIN)

        ZMQ_INIT = 1
        logger.success('server was initialized')

        keep_routing = True 
        client_accumulator = {}
        while keep_routing:
            logger.debug(f'server is listening at port : {router_port}')
            key_code = cv2.waitKey(10) & 0xFF  # 10ms
            keep_routing = key_code != 27   # hit the [escape] button to break the loop  
            incoming_events = dict(router_socket_poller.poll(100)) # wait 100ms to check if there is an incoming stream 
            router_socket_status = incoming_events.get(router_socket, None)
            if router_socket_status is not None: 
                if router_socket_status == zmq.POLLIN: 
                    # there is an incoming stream 
                    client_id, delimeter, message_type, message_data = router_socket.recv_multipart()  # blocked 
                    if message_type == b'join':
                        logger.debug(f'{client_id} has join the chanel')
                        router_socket.send_multipart([client_id, delimeter, b'accp', b''])
                        nb_clients = len(client_accumulator)
                        client_accumulator[client_id] = {
                            'status': 1, 
                            'screen': f'{nb_clients:05d}'  # 0 => 000000
                        }
                        create_window(client_accumulator[client_id]['screen'])
                    if message_type == b'data':
                        client_data = client_accumulator.get(client_id, None)
                        if client_data['status'] == 1: 
                            decoded_image = pickle.loads(message_data)
                            cv2.imshow(client_data['screen'], decoded_image)
                    if message_type == b'exit':
                        client_data = client_accumulator.get(client_id, None)
                        cv2.destroyWindow(client_data['screen'])
                        del client_accumulator[client_id]  # remove client form the map 
            else: 
                pass 
        # end loop routing ...! 
        cv2.destroyAllWindows()  
    except KeyboardInterrupt:
        pass 
    except Exception as e:
        logger.error(e)
    finally:
        if ZMQ_INIT == 1:
            router_socket_poller.unregister(router_socket)
            router_socket.close() 
            ctx.term()
            logger.success('server has removed all ressources')

if __name__ == '__main__':
    serving()