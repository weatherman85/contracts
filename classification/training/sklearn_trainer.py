from classification.training.tune import tune_model
import logging
import logging.handlers
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score,classification_report
import pickle, joblib
import random
from sklearn.model_selection import GridSearchCV, train_test_split

import classification.training.loggers as loggers

def train_model(train: pd.DataFrame,
                features: str,
                labels: str,
                vect: str = "count",
                test: pd.DataFrame = None,
                classifier: str = None,
                size: float = 0.2,
                log_path: str = None,
                tune: bool = False) -> dict:

    loggers.configure_logging(log_path=log_path, verbose=True)
    root_logger = logging.getLogger()

    le = LabelEncoder()
    le.fit(train[labels])
    train_X = train[features]
    train_Y = le.transform(train[labels])

    if test is None:
        train_X, test_X, train_Y, test_Y = train_test_split(
            train_X, train_Y, test_size=size, random_state=1234
        )
    else:
        test_X = test[features]
        test_Y = test[labels]

    classifiers, vectorizers, classifiers_params, tf_idf_parameters = tune_model(tune=tune)

    results = {}
    output = {}

    if not classifier:
        for name in classifiers.keys():
            root_logger.info(f"Training {name} model with base parameters")
            cls = classifiers[name]
            parameters = {}
            if vect == "count":
                text_clf = Pipeline([
                    ('vect', CountVectorizer()),
                    ('tfidf', TfidfTransformer()),
                    ("clf", cls)
                ])
                parameters.update(tf_idf_parameters["count"])
                parameters.update(tf_idf_parameters["tfidf"])
                parameters.update(classifiers_params[name])
            elif vect == "doc2vec":
                text_clf = Pipeline([
                    # ("vect",Doc2VecModel()),
                    ("clf", cls)
                ])
            else:
                raise ValueError("Unsupported vectorization method.")

            text_clf.fit(train_X, train_Y)
            param = parameters
            predicted = text_clf.predict(test_X)
            predicted = le.inverse_transform(predicted)
            report = classification_report(test_Y, predicted)
            accuracy = accuracy_score(test_Y, predicted)
            root_logger.info(report)
            results.update({name: {
                "model": text_clf,
                "params": param,
                "labels": le.classes_,
                "accuracy": accuracy,
                "report": report,
                "label_encoder":le
            }})
            root_logger.info(f"{name} classifier model created with accuracy of {accuracy}.")
            parameters.clear()

        best_model_name = max(results, key=lambda v: results[v].get("accuracy", float("-inf")))
        if tune:
            root_logger.info(f"{best_model_name} selected as best model with accuracy of "
                             f"{results[best_model_name]['accuracy']}. Performing tuning on this model only")
            root_logger.info(f"Training {best_model_name} model with provided parameters")
            cls = classifiers[best_model_name]
            parameters = {}
            if vect == "count":
                text_clf = Pipeline([
                    ('vect', CountVectorizer()),
                    ('tfidf', TfidfTransformer()),
                    ("clf", cls)
                ])
                parameters.update(tf_idf_parameters["count"])
                parameters.update(tf_idf_parameters["tfidf"])
                parameters.update(classifiers_params[best_model_name])
            elif vect == "doc2vec":
                text_clf = Pipeline([
                    # ("vect",Doc2VecModel()),
                    ("clf", cls)
                ])
            else:
                raise ValueError("Unsupported vectorization method.")

            gs_clf = GridSearchCV(text_clf,
                                  param_grid=parameters,
                                  cv=5,
                                  verbose=3,
                                  error_score="raise")
            gs_clf = gs_clf.fit(train_X, train_Y)

            root_logger.info(f"Best Test Score = {gs_clf.best_score_}")
            best_params = gs_clf.best_params_
            root_logger.info(f"The best parameters found: {best_params}")

            best_estimator = gs_clf.best_estimator_
            predicted = best_estimator.predict(test_X)
            predicted = le.inverse_transform(predicted)
            report = classification_report(test_Y, predicted)
            accuracy = accuracy_score(test_Y, predicted)
            root_logger.info(report)
            results[best_model_name] = {
                "model": best_estimator,
                "params": best_params,
                "labels": le.classes_,
                "accuracy": accuracy,
                "report": report,
                "label_encoder":le
            }
            root_logger.info(f"{best_model_name} classifier model created with accuracy of {accuracy}.")
            parameters.clear()

            output[best_model_name] = results[best_model_name]
            return output

    else:
        cls = classifiers[classifier]
        parameters = {}
        if vect == "count":
            text_clf = Pipeline([
                ('vect', CountVectorizer()),
                ('tfidf', TfidfTransformer()),
                ("clf", cls)
            ])
            parameters.update(tf_idf_parameters["count"])
            parameters.update(tf_idf_parameters["tfidf"])
            parameters.update(classifiers_params[classifier])
        elif vect == "doc2vec":
            text_clf = Pipeline([
                # ("vect",Doc2VecModel()),
                ("clf", cls)
            ])
        else:
            raise ValueError("Unsupported vectorization method.")
        root_logger.info(f"Training {classifier} model with base parameters")

        if tune:
            classifiers, vectorizers, classifiers_params, tf_idf_parameters = tune_model(tune=True)
            cls = classifiers[classifier]
            parameters = {}
            if vect == "count":
                text_clf = Pipeline([
                    ('vect', CountVectorizer()),
                    ('tfidf', TfidfTransformer()),
                    ("clf", cls)
                ])
                parameters.update(tf_idf_parameters["count"])
                parameters.update(tf_idf_parameters["tfidf"])
                parameters.update(classifiers_params[classifier])
            elif vect == "doc2vec":
                text_clf = Pipeline([
                    # ("vect",Doc2VecModel()),
                    ("clf", cls)
                ])
            else:
                raise ValueError("Unsupported vectorization method.")

            gs_clf = GridSearchCV(text_clf,
                                    param_grid=parameters,
                                    cv=5,
                                    verbose=3,
                                    error_score="raise")
            gs_clf = gs_clf.fit(train_X, train_Y)

            root_logger.info(f"Best Test Score = {gs_clf.best_score_}")
            best_params = gs_clf.best_params_
            root_logger.info(f"The best parameters found: {best_params}")

            best_estimator = gs_clf.best_estimator_
        else:
            text_clf.fit(train_X, train_Y)
            best_params = parameters
            best_estimator = text_clf

        predicted = best_estimator.predict(test_X)
        predicted = le.inverse_transform(predicted)
        report = classification_report(test_Y, predicted)
        accuracy = accuracy_score(test_Y, predicted)
        root_logger.info(report)
        results[classifier] = {
            "model": best_estimator,
            "params": best_params,
            "labels": le.classes_,
            "accuracy": accuracy,
            "report": report,
            "label_encoder":le
        }
        root_logger.info(f"{classifier} classifier model created with accuracy of {accuracy}.")

        parameters.clear()

    output[classifier] = results[classifier]
    return output

def save_model(name, model, train_data, path):
    # Save the trained model
    model_output_path = f"{path}/{name}_model.pkl"
    with open(model_output_path, 'wb') as model_output:
        joblib.dump(model, model_output)
    
    # Save the training data to an Excel file
    train_data_output_path = f'{path}/{name}_train_data.xlsx'
    train_data.to_excel(train_data_output_path, index=False)
