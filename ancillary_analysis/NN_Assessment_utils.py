from sklearn.neighbors import NearestNeighbors
from sklearn.neighbors import KNeighborsClassifier
import numpy as np
from sklearn.metrics import f1_score, recall_score, precision_score, roc_auc_score,accuracy_score
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import StratifiedKFold
import os
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import umap
import itertools
from Bio import pairwise2
import numpy as np
from Bio.pairwise2 import format_alignment
from multiprocessing import Pool
import colorsys
import matplotlib.patches as mpatches



def KNN(distances,labels,k=1):
    lb = LabelEncoder()
    labels = lb.fit_transform(labels)

    skf = StratifiedKFold(n_splits=5, random_state=None, shuffle=True)
    neigh = KNeighborsClassifier(n_neighbors=k, metric='precomputed', weights='distance')

    pred_list = []
    pred_prob_list = []
    labels_list = []
    for train_idx, test_idx in skf.split(distances,labels):
        distances_train = distances[train_idx, :]
        distances_train = distances_train[:, train_idx]

        distances_test = distances[test_idx, :]
        distances_test = distances_test[:, train_idx]

        labels_train = labels[train_idx]
        labels_test = labels[test_idx]

        neigh.fit(distances_train, labels_train)
        pred = neigh.predict(distances_test)
        pred_prob = neigh.predict_proba(distances_test)

        labels_list.extend(labels_test)
        pred_list.extend(pred)
        pred_prob_list.extend(pred_prob)

    pred = np.asarray(pred_list)
    pred_prob = np.asarray(pred_prob_list)
    labels = np.asarray(labels_list)

    OH = OneHotEncoder(sparse=False)
    labels = OH.fit_transform(labels.reshape(-1,1))
    pred = OH.transform(pred.reshape(-1,1))

    recall = []
    precision = []
    f_score = []
    auc_score = []
    acc_score = []
    for ii,c in enumerate(lb.classes_):
        recall.append(recall_score(y_true=labels[:,ii],y_pred=pred[:,ii]))
        precision.append(precision_score(y_true=labels[:,ii],y_pred=pred[:,ii]))
        f_score.append(f1_score(y_true=labels[:, ii], y_pred=pred[:,ii]))
        auc_score.append(roc_auc_score(labels[:, ii],pred_prob[:,ii]))
        acc_score.append(accuracy_score(y_true=labels[:,ii],y_pred=pred[:,ii]))

    return lb.classes_,recall, precision,f_score,auc_score,acc_score

def Assess_Performance(DTCRU, distances_vae_seq, distances_vae_seq_gene, distances_hamming, distances_kmer,distances_seqalign,dir_results,use_genes_label='use_genes'):
    labels = DTCRU.label_id
    k_values = list(range(1, 500, 25))
    rep = 5
    temp = []
    for v in k_values:
        temp.extend(rep*[v])
    k_values = temp
    class_list = []
    recall_list = []
    precision_list = []
    f1_score_list = []
    accuracy_list = []
    auc_list = []
    algorithm = []
    k_list = []
    use_genes_list=[]

    for k in k_values:
        # Collect performance metrics for various methods
        # VAE Seq
        classes, recall, precision, f1_score, auc,acc = KNN(distances_vae_seq, labels, k=k)
        class_list.extend(classes)
        recall_list.extend(recall)
        precision_list.extend(precision)
        f1_score_list.extend(f1_score)
        accuracy_list.extend(acc)
        auc_list.extend(auc)
        algorithm.extend(len(classes) * ['VAE_Seq'])
        k_list.extend(len(classes) * [k])
        use_genes_list.extend(len(classes)*[use_genes_label])

        # VAE Seq Gene
        classes, recall, precision, f1_score, auc,acc = KNN(distances_vae_seq_gene, labels, k=k)
        class_list.extend(classes)
        recall_list.extend(recall)
        precision_list.extend(precision)
        f1_score_list.extend(f1_score)
        accuracy_list.extend(acc)
        auc_list.extend(auc)
        algorithm.extend(len(classes) * ['VAE_Seq_Gene'])
        k_list.extend(len(classes) * [k])
        use_genes_list.extend(len(classes)*[use_genes_label])

        # Hamming Distance
        classes, recall, precision, f1_score, auc,acc = KNN(distances_hamming, labels, k=k)
        class_list.extend(classes)
        recall_list.extend(recall)
        precision_list.extend(precision)
        f1_score_list.extend(f1_score)
        auc_list.extend(auc)
        accuracy_list.extend(acc)
        algorithm.extend(len(classes) * ['Hamming'])
        k_list.extend(len(classes) * [k])
        use_genes_list.extend(len(classes)*[use_genes_label])

        # Kmer search
        classes, recall, precision, f1_score, auc,acc = KNN(distances_kmer, labels, k=k)
        class_list.extend(classes)
        recall_list.extend(recall)
        precision_list.extend(precision)
        f1_score_list.extend(f1_score)
        auc_list.extend(auc)
        accuracy_list.extend(acc)
        algorithm.extend(len(classes) * ['K-Mer'])
        k_list.extend(len(classes) * [k])
        use_genes_list.extend(len(classes)*[use_genes_label])

        #Sequence Alignment
        classes,recall, precision, f1_score,auc,acc = KNN(distances_seqalign,labels,k=k)
        class_list.extend(classes)
        recall_list.extend(recall)
        precision_list.extend(precision)
        f1_score_list.extend(f1_score)
        auc_list.extend(auc)
        accuracy_list.extend(acc)
        algorithm.extend(len(classes)*['Global Seq-Align'])
        k_list.extend(len(classes)*[k])
        use_genes_list.extend(len(classes)*[use_genes_label])

    df_out = pd.DataFrame()
    df_out['Classes'] = class_list
    df_out['Recall'] = recall_list
    df_out['Precision'] = precision_list
    df_out['F1_Score'] = f1_score_list
    df_out['Accuracy'] = accuracy_list
    df_out['AUC'] = auc_list
    df_out['Algorithm'] = algorithm
    df_out['k'] = k_list
    df_out['Gene_Usage'] = use_genes_list
    if not os.path.exists(dir_results):
        os.makedirs(dir_results)
    df_out.to_csv(os.path.join(dir_results,'df.csv'),index=False)

    return df_out

def Plot_Performance(df,dir_results):
    subdir = 'Performance'
    if not os.path.exists(os.path.join(dir_results,subdir)):
        os.makedirs(os.path.join(dir_results,subdir))

    measurements = ['Recall', 'Precision', 'F1_Score']
    types = np.unique(df['Classes'].tolist())
    for m in measurements:
        for t in types:
            sns.catplot(x='k',y=m,data=df[df['Classes']==t],kind='point',hue='Algorithm',capsize=0.2)
            plt.title(t)
            plt.subplots_adjust(top=0.9)
            plt.savefig(os.path.join(dir_results,subdir,m+'_'+t+'.tif'))

def Plot_Latent(labels,methods,dir_results):
    subdir = 'Latent'
    if not os.path.exists(os.path.join(dir_results,subdir)):
        os.makedirs(os.path.join(dir_results,subdir))

    N = len(np.unique(labels))
    HSV_tuples = [(x * 1.0 / N, 1.0, 0.5) for x in range(N)]
    np.random.shuffle(HSV_tuples)
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    color_dict = dict(zip(np.unique(labels), RGB_tuples))

    patches = []
    for item in color_dict.items():
        patches.append(mpatches.Patch(color=item[1], label=item[0]))

    c = [color_dict[x] for x in labels]
    names = ['VAE-Seq', 'VAE-Seq-Gene', 'Hamming', 'K-mer','Global Seq-Align']
    for m, n in zip(methods, names):
        X_2 = umap.UMAP(metric='precomputed').fit_transform(m)
        plt.figure()
        plt.scatter(X_2[:, 0], X_2[:, 1], c=c,s=100,alpha=0.75,label=labels)
        plt.title(n)
        plt.legend(handles=patches)
        plt.savefig(os.path.join(dir_results,subdir,n+'_latent.tif'))


def kmer_search(sequences):
    all = []
    for seq in sequences:
        all.extend(seq)
    all = list(set(all))

    mers = list(itertools.product(all, repeat=3))
    matrix = np.zeros(shape=[len(sequences), len(mers)])

    for ii, seq in enumerate(sequences, 0):
        for jj, m in enumerate(mers, 0):
            matrix[ii, jj] = seq.count(''.join(m))

    matrix = matrix[:,np.sum(matrix,0)>0]

    return matrix

def get_score(a,b):
    s_12 =  pairwise2.align.globalxx(a, b)[-1][-1]
    s_11 =  pairwise2.align.globalxx(a, a)[-1][-1]
    s_22 =  pairwise2.align.globalxx(b, b)[-1][-1]
    return (1-s_12/s_11)*(1-s_12/s_22)

def pairwise_alignment(sequences):
    matrix = np.zeros(shape=[len(sequences), len(sequences)])
    seq_1 = []
    seq_2 = []
    for ii,a in enumerate(sequences,0):
        for jj,b in enumerate(sequences,0):
            seq_1.append(a)
            seq_2.append(b)

    args = list(zip(seq_1,seq_2))
    p = Pool(40)
    result = p.starmap(get_score, args)

    p.close()
    p.join()

    i=0
    for ii,a in enumerate(sequences,0):
        for jj,b in enumerate(sequences,0):
            matrix[ii,jj] = result[i]
            i+=1

    return matrix




