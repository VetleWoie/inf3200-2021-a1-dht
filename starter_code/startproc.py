from os import path
from subprocess import Popen, PIPE
from signal import SIGINT, signal, SIGTERM
import sys

PROCS = []
NODES = []

def signal_handle(signum, frame):
    print("Terminating processes")
    for p in PROCS:
        p.send_signal(SIGTERM)
        exit()

def run_local(num_nodes,port, cont=False):
    signal(SIGTERM, signal_handle)
    signal(SIGINT, signal_handle)

    commands = []
    
    ip = "127.0.0.1:"
    ports = []
    for i in range(port, port + num_nodes):
        ports.append(ip + str(i))

    command = ["python3", "node.py", "-p"]
    for i in range(num_nodes):
        tmp = ports[0]
        ports[0] = ports[i]
        ports[i] = tmp
        commands.append(command + [ports[0].split(":")[1]] + ports)

    for command in commands:
        print("Running command: ", command)
        PROCS.append(
            Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            )

    if not cont:
        while(True):
            if len(PROCS) == 0:
                break
            for p in PROCS:
                if p.poll() is None:
                    pass
                else:
                    #Check wether proces terminated by error
                    output, err = p.communicate()
                    print("Error: One proces exited with the following error:\n\n")
                    print(err.decode())
                    signal_handle(0,0)
    return PROCS

def findNodes(numNodes):
        ##Find available nodes
        with Popen(['sh','/share/apps/ifi/available-nodes.sh'], stdin=PIPE, stdout=PIPE, stderr=PIPE) as p: 
            availableNodes, err = p.communicate()
            availableNodes = availableNodes.decode().splitlines()

        if len(availableNodes) < numNodes:
            sys.stderr.write("Not enough available nodes. Availabe Nodes: " + str(len(availableNodes)) + " Got: " + str(numNodes) + "\n")
            exit()
        return availableNodes[:numNodes]

def run_cluster(num_nodes, port, cont=False):
    path = "/home/vho023/3200/inf3200-2021-a1-dht/starter_code"
    NODES = findNodes(num_nodes)
    neighbors = []
    for node in NODES:
        neighbors.append(f'{node}:{port}')
    
    command = []
    for i,node in enumerate(NODES):
        command = ["ssh", node, "python3", f"{path}/node.py", "-p", f"{port}"]
        tmp = neighbors[0]
        neighbors[0] = neighbors[i]
        neighbors[i] = tmp
        print(f"Running: {command+neighbors}")
        PROCS.append(Popen(command+neighbors,stdin=PIPE, stdout=PIPE, stderr=PIPE))
    
    if not cont:
        while(True):
            if len(PROCS) == 0:
                print("Exiting")
            for p in PROCS:
                if p.poll() is None:
                    pass
                else:
                    #Check wether proces terminated by error
                    output, err = p.communicate()
                    print("Error: One proces exited with the following error:\n\n")
                    print(err.decode())
                    signal_handle(0,0)
    return PROCS, NODES

def kill_cluster(nodes, user):
    for node in nodes:
        command = ['ssh', node.split(':')[0], 'killall', '-u', user]
        Popen(command,stdin=PIPE, stdout=PIPE, stderr=PIPE)
        

    

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} [local/cluster] [number of nodes] {{starter port}}")
        exit(1)
    
    if len(sys.argv) == 4:
        port = sys.argv[3]
    else:
        port = 64209

    num_nodes = int(sys.argv[2])
    if sys.argv[1].lower() in ['local', 'l']:
        run_local(num_nodes,port)
    elif sys.argv[1].lower() in ['cluster', 'c']:
        run_cluster(num_nodes, port)
    else:
        print("Error: Unknown run option")
        exit(-1)     
    
                    
        



