import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

DIR = 'measurements'
FILE = 'measurments_cluster.csv'

data = pd.read_csv(f"{DIR}/{FILE}")

mean = []
std = []
nodes = []
amount = data['Amount']
for i in data['Nodes']:
    nodes.append(i)
    mean.append(np.mean(amount/data.loc[data['Nodes'] == i]["Time"]))
    std.append(np.std(amount/data.loc[data['Nodes'] == i]["Time"]))


mean = np.array(mean)
std = np.array(std)
nodes = np.array(nodes)
fig, ax = plt.subplots(1,1)

ax.plot(nodes,mean, label = f"Avarage PUT-GET througput of {amount[0]} runs")
ax.plot(nodes,mean+std, label = "Avarage pluss standard deviation")
ax.plot(nodes,mean-std, label = "Avarage minus standard deviation")
ax.set_title("Througput of system in PUT+GET per seconds")
ax.set_xlabel("Nodes")
ax.set_ylabel("Througput: $\\frac{PUT+GET}{s}$")
ax.legend()
plt.savefig("plot_througput.pdf")
plt.close(fig)

mean = []
std = []
nodes = []
amount = data['Amount']
for i in data['Nodes']:
    nodes.append(i)
    mean.append(np.mean(data.loc[data['Nodes'] == i]["Time"]/amount))
    std.append(np.std(data.loc[data['Nodes'] == i]["Time"]/amount))


mean = np.array(mean)
std = np.array(std)
nodes = np.array(nodes)
fig, ax = plt.subplots(1,1)

ax.plot(nodes,mean, label = f"Avarage PUT-GET time of {amount[0]} runs")
ax.plot(nodes,mean+std, label = "Avarage pluss standard deviation")
ax.plot(nodes,mean-std, label = "Avarage minus standard deviation")
ax.set_title("Avarage response time of system for a PUT/GET pair")
ax.set_xlabel("Nodes")
ax.set_ylabel("Response time/s")
ax.legend()
plt.savefig("plot_time.pdf")
plt.close(fig)
