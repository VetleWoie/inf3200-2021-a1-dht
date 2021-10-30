#!/usr/bin/env python3
import argparse
from http.client import NOT_EXTENDED
import json
import re
import signal
import socket
import socketserver
import threading
import logging
from hashlib import sha1
import requests
import time
from http.server import BaseHTTPRequestHandler,HTTPServer

CHRASHED = False
M = 6
chord = -1

class Chord():
    def __init__(self, args):
        logging.info(f"Initializing chord ring")
        self.object_store = {}
        self.successor = -1
        self.predecessor = -1
        self.hostname = args.neighbors[0]
        self.id = self.find_key(self.hostname)

        self.create_ring()
        self.start_stabilize_timer()
        logging.debug(f"Succsessor: {self.successor}")
        logging.debug(f"Predecessor: {self.predecessor}")

    def start_stabilize_timer(self):
        self.stabilize_thread = threading.Thread(target=self.stabilize_timer, daemon=True)
        self.stabilize_thread.start()

    def stabilize_timer(self):
        while not CHRASHED:
            time.sleep(1)
            self.stabilize()
            self.check_predecessor()

    def create_ring(self,):
        self.predecessor = None
        self.successor = [self.id, self.hostname]

    def join(self,host):
        self.predecessor = None
        r = requests.get(f"http://{host}/successor/{self.hostname}")
        self.successor = [self.find_key, r.text]
        r = requests.post(f"http://{self.successor[1]}/notify/{self.hostname}")
        self.stabilize()
        return r.status_code, f"Connected to {self.successor[1]}"

    def stabilize(self,):
        #Ask for succsessors predecessor
        #IF succsessors predecessors is self, then ok
        # else change successor to succsessors predecessor
        r = requests.get(f"http://{self.successor[1]}/predecessor/")
        if r.status_code == 404 or r.status_code == 500:
            return
        successor_predecessor = self.find_key(r.text)
        if not successor_predecessor == self.id:
            self.successor[0] = successor_predecessor
            self.successor[1] = r.text
            r = requests.post(f"http://{self.successor[1]}/notify/{self.hostname}")

    def notify(self,possible_predecessor):
        #Someone thinks they might be our predeccessor
        #If predecessor is None or possible_predecessor is between self and current predecessor
        #Update predecessor
        predecessor_id = self.find_key(possible_predecessor)
        is_predecessor, _ = self.check_key(predecessor_id)
        if is_predecessor:
            self.predecessor = [predecessor_id, possible_predecessor]
            return 200, "Updated predecessor"
        else:
            return 400, "Not my predecessor"

    def successor_left(self, new_successor):
        logging.info(f"Updating to new successor: {new_successor}")
        self.successor[0] = self.find_key(new_successor)
        self.successor[1] = new_successor
        if(self.successor[0] != self.id):
            r = requests.post(f"http://{self.successor[1]}/notify/{self.hostname}")

    def predecessor_left(self):
        self.predecessor = None
    
    def leave(self):
        if self.successor[0] == self.id:
            logging.info("No ring to leave, I am alone")
            return 200, "No ring to leave"
        r = requests.delete(f"http://{self.successor[1]}/predecessor")
        if self.predecessor is not None:
            r = requests.delete(f"http://{self.predecessor[1]}/successor/{self.successor[1]}")
        logging.info("Notified succsessor and predecessor of leaving, starting own ring")
        self.create_ring()
        return 200, "Left ring and started own ring"
    
    def node_crash(self, hostname, successor):
        if self.find_key(hostname) == self.successor[0]:
            self.successor = [self.find_key(successor), successor]
            if not self.successor[0] == self.id:
                r = requests.post(f"http://{self.successor[1]}/notify/{self.hostname}")
        else:
            r = requests.delete(f"http://{self.successor[1]}/node_crash/{hostname}/{successor}")
        

    def check_predecessor(self,):
        #Check if predecessor is still available
        #Make dummy request
        if self.predecessor == None:
            return

        r = requests.get(f"http://{self.predecessor[1]}/predecessor/")
        if r.status_code == 500:
            predecessor = self.predecessor[1]
            self.predecessor = None
            self.node_crash(predecessor, self.hostname)

    def find_key(self,key):
        h = sha1()
        h.update(key.encode())
        return int(h.digest().hex(), base=16) % (2**M)

    def get_successor(self,):
        return self.successor[1]

    def get_predecessor(self,):
        return self.predecessor[1] if self.predecessor is not None else None

    def check_key(self,key):
        if self.predecessor is None:
            return True,None
        elif self.predecessor[0] > self.id:
            if key <= self.id or key > self.predecessor[0]:
                return True, None
            else:
                return False, self.successor[1]            
        else:
            if key <= self.id and key > self.predecessor[0]:
                return True, None
            else:
                return False, self.successor[1]
    
    def get_info(self):
        info = {
            "node_hash": hex(self.id),
            "successor": self.successor[1],
            "others": [self.predecessor] if self.predecessor is not None else [],
        }
        return json.dumps(info)

class NodeHttpHandler(BaseHTTPRequestHandler):

    def send_whole_response(self, code, content, content_type="text/plain", inter_com=False):
        global CHRASHED
        if CHRASHED and not inter_com:
            logging.info("Simulating crash: returning code 500")
            code = 500
            content = ""
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
    
    def extract_host_from_path(self, path):
        return path.split('=')[1]

    def do_PUT(self):
        content_length = int(self.headers.get('content-length', 0))
        content_type = self.headers.get('Content-type',0)

        extern_key = self.extract_key_from_path(self.path)
        key = chord.find_key(extern_key)
        logging.debug(f"PUT:key id: {key}, my id: {chord.id}")
        local_key, successor = chord.check_key(key)
        value = self.rfile.read(content_length)
        if local_key:
            logging.info(f"PUT: Storing value {value} of type {content_type} on intern key {key} extern key {extern_key}")
            chord.object_store[key] = value
            self.send_whole_response(200, f"Value stored for {str(extern_key)} \n")
        else:
            logging.info(f"PUT:Not local key, sending {value} on key {extern_key} to {successor}")
            r = requests.put(f"http://{successor}/storage/{extern_key}", data=value)
            logging.debug(f"PUT: Got status {r.status_code}, response: {r.text}")
            self.send_whole_response(r.status_code, r.text)

    def do_GET(self):
        logging.debug(f"GET: {self.path}")
        if self.path.startswith("/storage"):
            logging.debug("Get request recieved")
            extern_key = self.extract_key_from_path(self.path)
            key = chord.find_key(extern_key)
            local_key, successor = chord.check_key(key)
            logging.debug("local key and successor found")
            if local_key:
                if key in chord.object_store:
                    logging.info(f"GET:Responding with value {chord.object_store[key]} at intern key {key}")
                    self.send_whole_response(200, chord.object_store[key])
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
            response = [chord.get_successor(), chord.get_predecessor()]
            logging.info(f"GET: Responding with successors: {response}")
            self.send_whole_response(200, response)
        elif self.path.startswith("/66"):
            successor = chord.get_successor()
            logging.info(f"Got order 66, terminate {successor}")
            r = requests.get(f"http://{successor}/66")
            server.shutdown()
        elif self.path.startswith("/node-info"):
            info = chord.get_info()
            logging.info(f"GET: Infor requested, sending {info}")
            self.send_whole_response(200,info, content_type='application/json')
        elif self.path.startswith("/successor"):
            #Get ID of node trying to connect
            logging.info(f"GET:Node wants to connect to ring: {self.path.split('/')}")
            hostname = self.path.split('/')[2]
            #Check wether current node should be successor
            id = chord.find_key(hostname)
            logging.info(f"GET:Node with hostname {hostname} and ID {id} wants to join the circle")
            local_key, successor = chord.check_key(id)
            if local_key:
                self.send_whole_response(200, f"{chord.hostname}")
            else:
                logging.info(f"GET:Asking successor at {successor} wether ID {id} is its predecessor")
                r = requests.get(f"http://{successor}/successor/{hostname}")
                logging.debug(f"GET: Got status {r.status_code} response: {r.text}")
                self.send_whole_response(r.status_code, r.text)
        elif self.path.startswith("/predecessor"):
            # logging.info("GET:Request for predecessor recieved")
            predecessor = chord.get_predecessor()
            if predecessor is None:
                # logging.info("GET: Dont have a predecessor responding with 404")
                self.send_whole_response(404, "")
            else:
                # logging.info(f"GET: Found predecessor responding with {predecessor}")
                self.send_whole_response(200, predecessor)
        else:
            self.send_whole_response(404, "Unknown path: " + self.path)
    
    def do_POST(self):
        global CHRASHED
        if self.path.startswith("/join"):
            if CHRASHED:
                self.send_whole_response(500, "")
            host = self.extract_host_from_path(self.path)
            logging.info(f"POST:Joining ring at: {host}")
            code, message = chord.join(host)
            self.send_whole_response(code, message,inter_com=False)
        elif self.path.startswith("/leave"):
            if CHRASHED:
                self.send_whole_response(500, "")
            logging.info(f"POST: Leaving ring")
            code, message = chord.leave()
            self.send_whole_response(code, message,inter_com=False)
        elif self.path.startswith("/sim-crash"):
            logging.info("Simulating crash")
            CHRASHED = True
            self.send_whole_response(200, "Simulating chrash",inter_com=True)
        elif self.path.startswith("/sim-recover"):
            logging.info("Simulating recovery")
            CHRASHED = False
            successor = chord.get_successor()
            if not chord.find_key(successor) == chord.id:
                chord.create_ring()
                chord.start_stabilize_timer()
                chord.join(successor)
            self.send_whole_response(200, "Simulating recovery",inter_com=False)
        elif self.path.startswith("/notify"):
            if CHRASHED:
                self.send_whole_response(500, "")
            host = self.path.split('/')[2]
            # logging.info(f"POST: Got notified of possible predecessor from {host}")
            code, message = chord.notify(host)
            self.send_whole_response(code, message)
        else:
            logging.error("Unknown command")

    def do_DELETE(self):
        if self.path.startswith("/predecessor"):
            logging.info("DELETE: Predecessor leaving ring")
            chord.predecessor_left()
            self.send_whole_response(200, "")
        elif self.path.startswith("/successor"):
            logging.info("DELETE: Successor leaving ring")
            new_succesor = self.path.split('/')[2]  
            chord.successor_left(new_succesor)
            self.send_whole_response(200, "")
        elif self.path.startswith("/node_crash"):
            crashed_host = self.path.split('/')[2]
            successor = self.path.split('/')[3]
            logging.info(f"DELETE: Host {crashed_host} has chrashed, commencing cleanup")
            chord.node_crash(crashed_host, successor)
            self.send_whole_response(200, "")

            
            

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
    global chord

    logging.basicConfig(filename=f'logs/node_{args.port}.log', level=logging.INFO)
    server = ThreadingHttpServer(('', args.port), NodeHttpHandler)

    chord = Chord(args)
  
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
