from http.client import REQUESTED_RANGE_NOT_SATISFIABLE

from requests.models import ProtocolError
from startproc import run_cluster, run_local, kill_cluster
import signal
import time
import requests

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

if __name__ == '__main__':
    test_throughput(1,128,False)
