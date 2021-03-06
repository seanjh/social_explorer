import numpy as np

from sklearn.cluster import DBSCAN
from sklearn import metrics

# http://datasyndrome.com/post/69514893525/yelp-dataset-challenge-part-0-geographic
# Compute DBSCAN
def dbscan_cluster(data):
    X = data
    # X = StandardScaler().fit_transform(data)

    db = DBSCAN(eps=0.3, min_samples=10).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    print('Estimated number of clusters: %d' % n_clusters_)
    print("Silhouette Coefficient: %0.3f"
          % metrics.silhouette_score(X, labels))

    return labels, core_samples_mask, n_clusters_, X


# import matplotlib.pyplot as plt

# def plot_dbscan(labels, core_samples_mask, n_clusters_, X):
#     # Black removed and is used for noise instead.
#     unique_labels = set(labels)
#     colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
#     for k, col in zip(unique_labels, colors):
#         if k == -1:
#             # Black used for noise.
#             col = 'k'
#
#         class_member_mask = (labels == k)
#
#         xy = X[class_member_mask & core_samples_mask]
#         plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
#                  markeredgecolor='k', markersize=14)
#
#         xy = X[class_member_mask & ~core_samples_mask]
#         plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
#                  markeredgecolor='k', markersize=6)
#
#     plt.title('Estimated number of clusters: %d' % n_clusters_)
#     plt.show()