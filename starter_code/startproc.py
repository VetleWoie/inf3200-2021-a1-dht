from subprocess import Popen, PIPE 
from signal import SIGINT, signal, SIGTERM
import sys

PROCS = []

def signal_handle(signum, frame):
    print("Terminating processes")
    for p in PROCS:
        p.send_signal(SIGTERM)
        exit()
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [number of nodes] {{starter port}}")
        exit(1)
    
    if len(sys.argv) == 3:
        port = sys.argv[2]
    else:
        port = 8000
    
    signal(SIGTERM, signal_handle)
    signal(SIGINT, signal_handle)

    num_nodes = int(sys.argv[1])

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
                
        



