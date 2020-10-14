import pickle
from scipy.spatial import distance_matrix
import numpy as np
import umap
import umap.plot
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import DBSCAN
from util.editdistance import lcsdistance
from hdbscan import HDBSCAN

counterexamples = pickle.load(open('counterexamples_Problem12.p', 'rb'))

# good example
#counterexamples = [tuple(range(0, x)) for x in range(1,30)] + [tuple(range(0, x)) for x in range(60,100)]

labels = [c[0:2] for c in counterexamples]

for ce in sorted(counterexamples, key=lambda x: int(x[0])):
    print(ce)

def distance_matrix(counterexamples, penalty=0):
    n = len(counterexamples)
    m = np.zeros((n, n))

    for row in range(n):
        for col in range(n):
            m[row, col] = lcsdistance(counterexamples[row], counterexamples[col], penalty=penalty)

    return m

distmat = distance_matrix(counterexamples, penalty=3)
print(distmat)
#normalize
distmat = distmat / np.max(distmat)

#cluster_before = DBSCAN(metric="precomputed", eps=0.145, min_samples=3).fit_predict(distmat)
cluster_before = HDBSCAN(metric="precomputed", min_cluster_size=10, min_samples=1).fit_predict(distmat)
reducer = umap.UMAP(
    metric="precomputed",
    n_neighbors=len(counterexamples) - 1,
    min_dist=0.3,
)
embedding = reducer.fit(distmat)

cluster_after = HDBSCAN(metric='euclidean', min_cluster_size=20, min_samples=3).fit_predict(embedding.embedding_)

hover_data = pd.DataFrame({'index':np.arange(len(counterexamples)),
                           'label':[str(" ".join(c)) for c in counterexamples],
                           'cluster_before': cluster_before
                           })


fig = umap.plot.interactive(embedding, labels=cluster_after, hover_data=hover_data)
umap.plot.show(fig)

plt.scatter(
    embedding.embedding_[:, 0],
    embedding.embedding_[:, 1],
    label=cluster_after,
    c=cluster_after
)
plt.gca().set_aspect('equal', 'datalim')
plt.title("2D projection of clustered counterexamples")
plt.show()