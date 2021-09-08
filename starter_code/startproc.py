import subprocess
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [number of nodes] {{starter port}}")
        exit(1)
    
    if len(sys.argv) == 3:
        port = sys.argv[2]
    else:
        port = 8000
    
    ip = "127.0.0.1:"
    command = "python3 dummynode.py -p "
    ports = []

    tmp = port
    for i in range(sys.argv[1]):
        ports[i] = ip + str(tmp)
        tmp += 1

    nodestring = str(ports).replace(',', '').replace('[','').replace(']','')
    
    
