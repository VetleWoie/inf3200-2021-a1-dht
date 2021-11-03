from http.client import REQUESTED_RANGE_NOT_SATISFIABLE
from re import L
from typing import no_type_check_decorator

from requests.models import ProtocolError
from startproc import NODES, run_cluster, run_local, kill_cluster
import signal
import time
import requests
import json
import numpy as np

OUTDIR = 'measurements'
def do_get_put(amount, address, port):
    for i in range(amount):
        r = requests.put(f"http://{address}:{port}/storage/{i}", data="i")
        r = requests.get(f"http://{address}:{port}/storage/{i}")

def test_throughput(start, end, local):
    amount = 100
    if(local):
        address, port = "127.0.0.1", 64209
    else:
        address, port = "compute-0-1", 64209

    with open(f"{OUTDIR}/measurments_cluster.csv", 'w') as file:
        pass
    with open(f"{OUTDIR}/measurments_cluster.csv", 'a') as file:
        file.write("Nodes,Time,Amount\n")
        for i in range(start, end):
            procs, nodes = run_local(i, port,cont=True) if local else run_cluster(i, port, cont=True)
            for j in range(100):
                time.sleep(1)
                t1 = time.perf_counter()
                do_get_put(amount, nodes[0].split(':')[0], port)
                t2 = time.perf_counter()
                file.write(f"{i},{t2-t1},{amount}\n")
                time.sleep(1)
            if local:
                for proc in procs:
                    proc.send_signal(signal.SIGINT)
            else:
                kill_cluster(nodes, "vho023")
                for proc in procs:
                    proc.communicate()

def test_stability(node, ring_count):
    tmp = node
    for i in range(ring_count):
        # print(f"{tmp}->", end="")
        r = requests.get(f"http://{tmp}/node-info")
        tmp = json.loads(r.text)['successor']
        # print(tmp)
    return True if tmp == node else False

def test_alone(node):
    r = requests.get(f"http://{node}/node-info")
    if node == json.loads(r.text)['successor'] and len(json.loads(r.text)['others']) == 0:
        return True
    return False

def test_join_leave(start, end, step):
    join_time = {}
    leave_time = {}
    res_file = "bench_join_leave.csv"
    with open("Nodes.txt", 'r') as f:
        nodes = f.readlines()
    
    with open(res_file,'w') as f:
        f.write("Nodes,Join,Leave\n")
    
    for i in range(len(nodes)):
        nodes[i] = nodes[i].split("\n")[0]
    for num_nodes in range(start, end, step):
        for count in range(3):
            print(f"Running tests for {num_nodes}")
            #Make sure everybody is alone
            print("Telling everybody to leave")
            for node in nodes:
                r=requests.post(f"http://{node}/leave")
                if not test_alone(node):
                    print(f"{node} Not alone, trying again")
                    r=requests.post(f"http://{node}/leave")
            entry_host, entry_port = nodes[0].split(':') 

            print("Testing join")
            #Test join time
            t1 = time.perf_counter()
            for i in range(1,num_nodes):
                node = nodes[i]
                r = requests.post(f"http://{node}/join?nprime={entry_host}:{entry_port}")
                stable = test_stability(node, i+1)
                while not stable:
                    stable = test_stability(node, i+1)
            t2 = time.perf_counter()
            join = t2-t1
            join_time[num_nodes] = join

            print("Testing leave")
            #Test leave time
            t1 = time.perf_counter()
            for i in range(1,num_nodes//2):
                node = nodes[i]
                r=requests.post(f"http://{node}/leave")
                stable = test_stability(node, i+1)
                #Check that it has left
                if not test_alone(node):
                    print(f"{node} Not alone, trying again")
                    r=requests.post(f"http://{node}/leave")
                #Check stability
                while not stable:
                    stable = test_stability(nodes[0], i-1)
            t2 = time.perf_counter()
            leave = t2-t1
            leave_time[num_nodes] = leave            
            with open(res_file, 'a') as p:
                p.write(f"{num_nodes},{join},{leave}\n")
        
    print("Join Time: ",join_time)
    print("Leave Time: ", leave_time)

def join_nodes(amount):
    with open("Nodes.txt", 'r') as f:
        nodes = [node.split('\n')[0] for node in f.readlines()] 

    print("Joining nodes")
    entry_host, entry_port = nodes[0].split(':') 
    for i in range(1,amount):
        node = nodes[i]
        r = requests.post(f"http://{node}/join?nprime={entry_host}:{entry_port}")
        time.sleep(1)
    print("All nodes joined")

def test_chrash_resilience():
    with open("Nodes.txt", 'r') as f:
        nodes = [node.split('\n')[0] for node in f.readlines()]
    
    join_nodes(len(nodes))
    i=0
    while(test_stability(nodes[0], len(nodes)-i)):
        i += 1
        print(f"Trying {i} simulated chrashes")
        for node in range(1,i+1):
            print(f"\tTelling {nodes[node]} to chrash")
            r = requests.post(f"http://{nodes[node]}/sim-crash")
            print(r.text)
        time.sleep(1)
    print(f"Handled {i} nodes to chrash simultainously")

        
    


def print_successors(successor, successor_dict,nodes, init=False):
    print(successor, "->", successor_dict[successor])
    if not init and successor == nodes[1]:
        return 
    return print_successors(successor_dict[successor], successor_dict, nodes)

def test_sim_chrash_recover():
    pass
if __name__ == '__main__':
    # test_throughput(1,128,False)
    # test_join_leave(10, 51, 10)
    test_chrash_resilience()
