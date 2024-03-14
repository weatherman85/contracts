from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier

def tune_model(tune: bool = False, params: dict = None):
    classifiers = {
        "Nearest Neighbors": KNeighborsClassifier(),
        "Linear SVM": SVC(kernel="linear", probability=True),
        "Random Forest": RandomForestClassifier(),
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(),
        "SGD Classifier": SGDClassifier(),
        #"XGBoost": XGBClassifier()
    }
    
    vectorizers = {
        "count": CountVectorizer(),
        #"doc2vec": Doc2VecModel()
    }
    
    if tune and params is None:
        classifiers_params = {
            "Nearest Neighbors": {
                "clf__weights": ["uniform", "distance"],
                "clf__n_neighbors": [3, 5, 7, 9]
            },
            "Linear SVM": {
                "clf__C": [100],
                "clf__gamma": [0.001]
            },
            "Random Forest": {
                "clf__max_depth": [3, 5, 7, None],
                "clf__n_estimators": [5, 10, 15, 20],
                "clf__bootstrap": [True, False],
                "clf__criterion": ["gini", "entropy"],
            },
            "Naive Bayes": {
                "clf__alpha": [1, 0.1, 0.01, 0.001, 0.0001, 0.0001]
            },
            "SGD Classifier": {
                "clf__alpha": [1e-2, 1e-3],
                "clf__penalty": ["none", "l2", "l1", "elasticnet"],
                "clf__loss": ["log"]
            },
            "XGBoost": {
                "clf__max_depth": [2, 5, 10],
                "clf__n_estimators": [30, 50, 60, 120, 200],
                "clf__learning_rate": [0.1]
            },
            "Logistic Regression":{"clf__max_iter":[3000]}
        }
        
        tf_idf_parameters = {
            "count": {
                "vect__max_df": [0.5, 0.75, 0.9],
                "vect__ngram_range": [(1, 3)],
                "vect__max_features": [1000, 10000],
                "vect__stop_words": [None]
            },
            "doc2vec": {
                "vect__window": [2, 3],
                "vect__dm": [0, 1],
                "vect__size": [100, 200]
            },
            "tfidf": {
                "tfidf__use_idf": [True, False],
                "tfidf__norm": ["l2"],
                "tfidf__sublinear_tf": [True, False]
            }
        }
        
    else:
        classifiers_params = {
            "Nearest Neighbors": {
                "clf__weights": ["distance"],
                "clf__n_neighbors": [6]
            },
            "Linear SVM": {
                "clf__C": [100],
                "clf__gamma": [0.001],
                "clf__kernel": ["linear"]
            },
            "Random Forest": {
                "clf__max_depth": [None],
                "clf__n_estimators": [15],
                "clf__bootstrap": [True],
                "clf__criterion": ["entropy"]
            },
            "Naive Bayes": {
                "clf__alpha": [0.01]
            },
            "SGD Classifier": {
                "clf__alpha": [0.001],
                "clf__penalty": ["none"],
                "clf__max_iter": [20],
                "clf__loss": ["log"],
                "clf__tol": [1e-3]
            },
            "XGBoost": {
                "clf__n_estimators": [60],
                "clf__max_depth": [2],
                "clf__learning_rate": [.01]
            },
            "Logistic Regression":{"clf__max_iter":[3000]}
        }
        
        tf_idf_parameters = {
            "count": {
                "vect__max_df": [.75],
                "vect__ngram_range": [(1, 3)],
                "vect__max_features": [10000],
                "vect__stop_words": [None]
            },
            "doc2vec": {
                "vect__window": [2],
                "vect__dm": [0],
                "vect__size": [100]
            },
            "tfidf": {
                "tfidf__use_idf": [True],
                "tfidf__norm": ["l2"],
                "tfidf__sublinear_tf": [True]
            }
        }
        
    return classifiers, vectorizers, classifiers_params, tf_idf_parameters

    
    