#!/usr/bin/env python3
import argparse
import json
import re
import signal
import socket
import socketserver
import threading
import logging
from hashlib import sha1
import requests

from http.server import BaseHTTPRequestHandler,HTTPServer

object_store = {}
neighbors = {}
neighbor_ids = []
id = -1
m = 6

def find_key(key):
    h = sha1()
    h.update(key.encode())
    return int(h.digest().hex(), base=16) % (2**m)

def check_key(key):
    if id == 0:
        if key <= neighbor_ids[id] or key > neighbor_ids[id-1]:
            return True, None
        else:
            return False, neighbors[neighbor_ids[(id+1) % len(neighbor_ids)]]
    else:
        if key <= neighbor_ids[id] and key >= neighbor_ids[id-1]:
            return True, None
        else:
            return False, neighbors[neighbor_ids[(id+1) % len(neighbor_ids)]]

class NodeHttpHandler(BaseHTTPRequestHandler):

    def send_whole_response(self, code, content, content_type="text/plain"):

        if isinstance(content, str):
            content = content.encode("utf-8")
            if not content_type:
                content_type = "text/plain"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
        elif isinstance(content, bytes):
            if not content_type:
                content_type = "application/octet-stream"
        elif isinstance(content, object):
            content = json.dumps(content, indent=2)
            content += "\n"
            content = content.encode("utf-8")
            content_type = "application/json"

        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length',len(content))
        self.end_headers()
        self.wfile.write(content)

    def extract_key_from_path(self, path):
        return re.sub(r'/storage/?(\w+)', r'\1', path)

    def do_PUT(self):
        content_length = int(self.headers.get('content-length', 0))

        extern_key = self.extract_key_from_path(self.path)
        key = find_key(extern_key)
        logging.debug(f"PUT:key id: {key}, my id: {neighbor_ids[id]}")
        local_key, successor = check_key(key)
        value = self.rfile.read(content_length)
        if local_key:
            logging.info(f"PUT: Storing value {value} on intern key {key} extern key {extern_key}")
            object_store[key] = value
            self.send_whole_response(200, f"Value stored for {str(extern_key)} \n")
        else:
            logging.info(f"PUT:Not local key, sending {value} on key {extern_key} to {successor}")
            r = requests.put(f"http://{successor}/storage/{extern_key}", data=value)
            logging.debug(f"PUT: Got status {r.status_code}, response: {r.text}")
            self.send_whole_response(r.status_code, r.text)

    def do_GET(self):
        if self.path.startswith("/storage"):
            extern_key = self.extract_key_from_path(self.path)
            key = find_key(extern_key)
            local_key, successor = check_key(key)
            if local_key:
                if key in object_store:
                    logging.info(f"GET:Responding with value {object_store[key]} at intern key {key}")
                    self.send_whole_response(200, object_store[key])
                else:
                    logging.info(f"GET:No data stored at intern key {key}")
                    self.send_whole_response(404,
                        "No object with key '%s' in this system\n" % key)
            else:
                logging.debug(f"GET: Not my id, requesting from {successor}")
                r = requests.get(f"http://{successor}/storage/{extern_key}")
                logging.debug(f"GET: Got status {r.status_code} response: {r.text}")
                self.send_whole_response(r.status_code, r.text)

        elif self.path.startswith("/neighbors"):
            self.send_whole_response(200, neighbors)

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

def arg_parser():
    PORT_DEFAULT = 8000
    DIE_AFTER_SECONDS_DEFAULT = 20 * 60
    parser = argparse.ArgumentParser(prog="node", description="DHT Node")

    parser.add_argument("-p", "--port", type=int, default=PORT_DEFAULT,
            help="port number to listen on, default %d" % PORT_DEFAULT)

    parser.add_argument("--die-after-seconds", type=float,
            default=DIE_AFTER_SECONDS_DEFAULT,
            help="kill server after so many seconds have elapsed, " +
                "in case we forget or fail to kill it, " +
                "default %d (%d minutes)" % (DIE_AFTER_SECONDS_DEFAULT, DIE_AFTER_SECONDS_DEFAULT/60))

    parser.add_argument("neighbors", type=str, nargs="*",
            help="addresses (host:port) of neighbour nodes")

    return parser

class ThreadingHttpServer(HTTPServer, socketserver.ThreadingMixIn):
    pass

def run_server(args):
    global server
    global neighbors
    global neighbor_ids
    global id

    logging.basicConfig(filename=f'logs/node_{args.port}.log', level=logging.DEBUG)
    server = ThreadingHttpServer(('', args.port), NodeHttpHandler)
    
    id = find_key(args.neighbors[0])
    for neighbor in args.neighbors:
        neighbors[find_key(neighbor)] = neighbor
    
    neighbor_ids = list(neighbors.keys())
    neighbor_ids.sort()
    id = neighbor_ids.index(id) 
    logging.debug("NEIGHBORS:", neighbors)

    def server_main():
        logging.info("Starting server on port {}. Neighbors: {}".format(args.port, args.neighbors))
        server.serve_forever()
        logging.info("Server has shut down")

    def shutdown_server_on_signal(signum, frame):
        logging.info("We get signal (%s). Asking server to shut down" % signum)
        server.shutdown()

    # Start server in a new thread, because server HTTPServer.serve_forever()
    # and HTTPServer.shutdown() must be called from separate threads
    thread = threading.Thread(target=server_main)
    thread.daemon = True
    thread.start()

    # Shut down on kill (SIGTERM) and Ctrl-C (SIGINT)
    signal.signal(signal.SIGTERM, shutdown_server_on_signal)
    signal.signal(signal.SIGINT, shutdown_server_on_signal)

    # Wait on server thread, until timeout has elapsed
    #
    # Note: The timeout parameter here is also important for catching OS
    # signals, so do not remove it.
    #
    # Having a timeout to check for keeps the waiting thread active enough to
    # check for signals too. Without it, the waiting thread will block so
    # completely that it won't respond to Ctrl-C or SIGTERM. You'll only be
    # able to kill it with kill -9.
    thread.join(args.die_after_seconds)
    if thread.is_alive():
        logging.info("Reached %.3f second timeout. Asking server to shut down" % args.die_after_seconds)
        server.shutdown()

    logging.info("Exited cleanly")

if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    run_server(args)
