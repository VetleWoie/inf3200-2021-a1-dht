import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

DIR = '.'
FILE = 'bench_res_1255.csv'

data = pd.read_csv(f"{DIR}/{FILE}")

mean_join = []
std_join = []
mean_leave = []
std_leave = []
nodes = []
for i in data['Nodes']:
    if i in nodes:
        continue
    nodes.append(i)
    mean_join.append(np.mean(data.loc[data['Nodes'] == i]["Join"]))
    std_join.append(np.std(data.loc[data['Nodes'] == i]["Join"]))
    mean_leave.append(np.mean(data.loc[data['Nodes'] == i]["Leave"]))
    std_leave.append(np.std(data.loc[data['Nodes'] == i]["Leave"]))
    


mean_join = np.array(mean_join)
std_join = np.full(mean_join.shape,np.mean(std_join))
mean_leave = np.array(mean_leave)
std_leave = np.full(mean_leave.shape,np.mean(std_leave))


nodes = np.array(nodes)
fig, ax = plt.subplots(1,1)
ax.plot(nodes, mean_join, label="Avarage time joining nodes")
ax.plot(nodes, mean_join+std_join, color='orange')
ax.plot(nodes, mean_join-std_join, color='orange')
ax.set_xlabel("Node joins")
ax.set_ylabel("Time")
ax.legend()
plt.savefig("join.png")

fig, ax = plt.subplots(1,1)
ax.plot(nodes, mean_leave, label="Avarage time halving nodes with leave")
ax.plot(nodes, mean_leave+std_leave, color='orange')
ax.plot(nodes, mean_leave-std_leave, color='orange')
ax.set_xlabel("Nodes in network at beginning of test")
ax.set_ylabel("Time")
ax.legend()
plt.savefig("leave.png")
plt.close(fig)
