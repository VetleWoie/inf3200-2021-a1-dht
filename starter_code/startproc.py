from subprocess import Popen, PIPE 
from signal import SIGINT, signal, SIGTERM
import sys

PROCS = []

def signal_handle(signum, frame):
    print("Terminating processes")
    for p in PROCS:
        p.send_signal(SIGTERM)
        exit()

def run_local(num_nodes,start_port):
    signal(SIGTERM, signal_handle)
    signal(SIGINT, signal_handle)

    commands = []
    
    ip = "127.0.0.1:"
    ports = []
    for i in range(port, port + num_nodes):
        ports.append(ip + str(i))

    command = ["python3", "dummynode.py", "-p"]
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

def run_cluster():
    pass

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
    
                    
        



