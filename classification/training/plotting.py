import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

def plot_confusion_matrix(y,y_predict,labels):
    cm = confusion_matrix(y,y_predict)
    ax = plt.subplot()
    sns.heatmap(cm,annot=True,ax=ax,cmpa="Blues")
    ax.set_xlabel("Predicted labels")
    ax.set_ylabel("True labels")
    ax.set_title('Confusion Matrix')
    ax.xaxis.set_ticklabels(labels); ax.yaxis.set_ticklabels(labels)
    plt.show()
    
