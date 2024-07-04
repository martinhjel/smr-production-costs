import numpy as np
import plotly.express as px
import plotly.graph_objects as go


c_lmr = 6000
p_lmr = 1100
p_smr = 225
betha = 0.55


# %% Roulestone
def roulestone(c_lmr, p_smr, p_lmr, betha):
    return c_lmr * ((p_smr / p_lmr) ** (betha - 1))


c_smr = roulestone(c_lmr, p_smr, p_lmr, betha)


def roulestone_with_learning(c_lmr, p_smr, p_lmr, betha, learning_rate, n):
    n = np.array(n)
    if n.any() < 1:
        raise ValueError("'n' lower than 1 is meaningless.")
    else:
        return roulestone(c_lmr, p_smr, p_lmr, betha) * (1 - learning_rate) ** (np.log2(n))


learning_rate = 0.05
n = 100
c_smr_n = roulestone_with_learning(c_lmr, p_smr, p_lmr, betha, learning_rate, n)

n = np.linspace(1, 1000)
c_smr_n = roulestone_with_learning(c_lmr, p_smr, p_lmr, betha, learning_rate, n)

px.line(x=n, y=c_smr_n)

betha=0.5
p_ratio = np.linspace(0,1,num=50)

data = []
for betha in np.linspace(0.2,0.75,num=10):
    C_ratio = p_ratio**(betha-1)
    data.append(go.Scatter(x=p_ratio,y=C_ratio,name=f"betha: {betha}"))

layout = go.Layout(title="Roulestone", xaxis=dict(title="P_smr/P_lmr"), yaxis=dict(title="c_smr/c_lmr", range=[0.9,5]))

fig = go.Figure(data=data, layout=layout)
fig.show()


# %% Rothwell


def rothwell(c_lmr, p_smr, p_lmr, gamma):
    return c_lmr * (p_smr / p_lmr) * gamma ** ((np.log(p_smr) - np.log(p_lmr)) / np.log(2))


def rotwhell_with_learning(c_lmr, p_smr, p_lmr, gamma, learning_rate, n):
    n = np.array(n)
    if n.any() < 1:
        raise ValueError("'n' lower than 1 is meaningless.")
    else:
        return rothwell(c_lmr, p_smr, p_lmr, gamma) * (1 - learning_rate) ** (np.log2(n))

gamma=0.5
p_ratio = np.linspace(0,1,num=50)

data = []
for gamma in np.linspace(0.2,0.75,num=10):
    betha = 1 + np.log2(gamma)
    C_ratio = p_ratio**(betha-1)
    data.append(go.Scatter(x=p_ratio,y=C_ratio,name=f"gamma: {betha}"))

layout = go.Layout(title="Rothwell", xaxis=dict(title="P_smr/P_lmr"), yaxis=dict(title="c_smr/c_lmr", range=[0.9,5]))

fig = go.Figure(data=data, layout=layout)
fig.show()


#%% Rothwell -> Roulestone

def rothwell_to_roulestone(gamma):
    betha = 1 + np.log(gamma)/np.log(2)
    return betha

#%% Roulestone -> Rothwell

def roulestone_to_rothwell(betha):
    gamma = 2**(betha-1)
    return gamma
# %%

betha = rothwell_to_roulestone(0.9)

roulestone(c_lmr, p_smr, p_lmr, betha)
