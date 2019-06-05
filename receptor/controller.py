import asyncio
import logging
import socket
import sys
import os

from . import protocol

logger = logging.getLogger(__name__)


def send_directive(directive, recipient, payload, socket_path):
    if payload == '-':
        payload = sys.stdin.read()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    sock.sendall(f"{recipient}\n{directive}\n{payload}".encode('utf-8') + protocol.DELIM)
    response = b''
    while True:
        part = sock.recv(4096)
        response += part
        if len(part) < 4096:
            # either 0 or end of data
            break
    sys.stdout.buffer.write(response + b"\n")


def mainloop(receptor, address, port, socket_path, loop=asyncio.get_event_loop()):
    listener = loop.create_server(
        lambda: protocol.BasicProtocol(receptor, loop),
        address, port)
    logger.info("Serving on %s:%s", address, port)
    loop.create_task(listener)
    control_listener = loop.create_unix_server(
        lambda: protocol.BasicControllerProtocol(receptor, loop),
        path=socket_path
    )
    logger.info(f'Opening control socket on {socket_path}')
    loop.create_task(control_listener)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        os.remove(socket_path)
