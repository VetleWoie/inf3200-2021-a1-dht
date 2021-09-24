from http.client import REQUESTED_RANGE_NOT_SATISFIABLE

from requests.models import ProtocolError
from startproc import run_cluster, run_local, kill_cluster
import signal
import time
import requests

def do_get_put(amount, address, port):
    for i in range(amount):
        r = requests.put(f"http://{address}:{port}/storage/{i}", data="i")
        r = requests.get(f"http://{address}:{port}/storage/{i}")
        print(r.text)

def test_throughput(start, end, local):
    amount = 5
    if(local):
        address, port = "127.0.0.1", 64209
    else:
        address, port = "compute-0-1", 64209

    with open("measurments_local.csv", 'w') as file:
        pass
    with open("measurments_local.csv", 'a') as file:
        file.write("Nodes time amount\n")
        for i in range(start, end):
            procs, nodes = run_local(i, port,cont=True) if local else run_cluster(i, port, cont=True)
            print(f"Timing {i}")
            t1 = time.perf_counter_ns()
            do_get_put(amount, address, port)
            t2 = time.perf_counter_ns()
            print(f"Done timing {i}")
            file.write(f"{i},{t2-t1},{amount}\n")
            time.sleep(1)
            if local:
                for proc in procs:
                    proc.send_signal(signal.SIGINT)
            else:
                kill_cluster(nodes, "vho023")

if __name__ == '__main__':
    test_throughput(1,16,False)