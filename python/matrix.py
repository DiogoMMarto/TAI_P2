import argparse

from meta import parse_database , open_file, Model , print_log
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
import umap 

def build_matrix(sequences: list[tuple[str,str]], k: int, alpha: float)-> np.ndarray:
    matrix = np.zeros((len(sequences),len(sequences)),dtype=np.float32)
    for i in range(len(sequences)):
        model = Model(sequences[i][1], k, alpha)
        print_log(f"[INFO] Model {i}: {sequences[i][0]}")
        for j in range(len(sequences)):
            if i != j:
                matrix[i][j] = model.nrc(sequences[j][1])
    return matrix

def visualize(nrc_matrix, labels_name=None, new_row=None, trim_indexes=None):
    
    dist_matrix = nrc_matrix + nrc_matrix.T  # Make it symmetric
    dist_matrix /= 2  # Average the two halves

    dist_matrix = np.vstack((dist_matrix, new_row))  
    new_row_plus_0 = np.zeros((1, dist_matrix.shape[1]+1), dtype=np.float32)
    new_row_plus_0[0, :-1] = new_row
    new_row_plus_0 = new_row_plus_0.T
    dist_matrix = np.concatenate((dist_matrix, new_row_plus_0), axis=1)
    
    twoD = True
    # Reduce dimensionality for visualization
    if twoD:
        tsne = TSNE(n_components=2, metric='precomputed', init='random', random_state=42)
        # umap_model = umap.UMAP(n_components=2, metric='precomputed', random_state=42)
    else:
        tsne = TSNE(n_components=3, metric='precomputed', init='random', random_state=42)
        # umap_model = umap.UMAP(n_components=3, metric='precomputed', random_state=42)
    coords = tsne.fit_transform(dist_matrix)

    # Plot clusters
    if twoD:
        plt.figure(figsize=(12, 8))
        # color based on new_row value being 0 red and 1 blue and values in between a gradient
        plt.scatter(coords[:-1, 0], coords[:-1, 1], c=new_row, cmap='viridis', marker='o')
        plt.colorbar(label='NRCS Value to Meta')        
        if labels_name is not None:
            for i, label in enumerate(labels_name):
                plt.annotate(label, (coords[i, 0], coords[i, 1]), fontsize=8)
        plt.xlabel('t-SNE 1')
        plt.ylabel('t-SNE 2')
        plt.scatter(coords[-1, 0], coords[-1, 1], color='red', s=100)
        plt.annotate("Meta", (coords[-1, 0], coords[-1, 1]), fontsize=8, color='red')
        plt.title('t-SNE Visualization')
        plt.show()
    else:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(coords[:-1, 0], coords[:-1, 1], coords[:-1, 2], marker='o')
        if labels_name is not None:
            for i, label in enumerate(labels_name):
                ax.text(coords[i, 0], coords[i, 1], coords[i, 2], label, fontsize=8)
        ax.set_xlabel('t-SNE 1')
        ax.set_ylabel('t-SNE 2')
        ax.set_zlabel('t-SNE 3')
        ax.set_title('Hierarchical Clustering and t-SNE Visualization')
        ax.scatter(coords[-1, 0], coords[-1, 1], coords[-1, 2], color='red', s=100)
        ax.text(coords[-1, 0], coords[-1, 1], coords[-1, 2], "New Sequence", fontsize=8, color='red')
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="MetaClass: find similar sequences.")
    parser.add_argument("-m","--matrix", type=str, required=True, help="Matrix file")
    parser.add_argument("-s","--sequence", type=str, required=True, help="Sequences file")
    parser.add_argument("-d","--data", type=str, required=True, help="Database file")
    parser.add_argument("-k","--context", type=int, default=2 , help="Depth of the context")
    parser.add_argument("-a","--alpha", type=float, default=1.0 , help="Smoothing factor")
    parser.add_argument("-v","--verbose", action="store_true", help="Print verbose")
    
    args = parser.parse_args()
    
    database_text = open_file(args.data)
    sequences = parse_database(database_text)
    if args.verbose:
        print_log(f"[INFO] Database: loaded {len(sequences)} sequences")
    
    if args.matrix:
        matrix = np.load(args.matrix)
    else:
        matrix = build_matrix(sequences, args.context, args.alpha)
    
    sequence_text = open_file(args.sequence)
    sequence_text = "".join([c for c in sequence_text if c in "ACGT"])
    
    model = Model(sequence_text, args.context, args.alpha)
    nrcs = np.zeros((1, len(sequences)), dtype=np.float32)
    for i in range(len(sequences)):
        nrcs[0][i] = model.nrc(sequences[i][1])
            
    if args.verbose:
        print_log(f"[INFO] Matrix: built {len(sequences)}x{len(sequences)} matrix")
        
    if args.matrix is None:
        np.save("matrix.npy", matrix)
    
    trim_ = 7
    for i in sorted(range(len(sequences)), key=lambda x: nrcs[0][x])[:trim_]:
        print(f"{nrcs[0][i]:.4f}\t{sequences[i][0]}")
        
    nrcs_top = np.argsort(nrcs[0])[:trim_]
    labels_name = ["" for i in range(len(sequences))]
    for i in nrcs_top:
        labels_name[i] = sequences[i][0][:10]
  
    visualize(matrix, labels_name=labels_name, new_row=nrcs,trim_indexes=nrcs_top)
    
if __name__ == "__main__":
    main()