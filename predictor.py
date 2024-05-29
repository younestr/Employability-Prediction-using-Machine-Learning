import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
from sklearn.model_selection import GridSearchCV

class EmploymentPredictor:
    def __init__(self, data_path=None):
        self.data_path = data_path
        self.data = None
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()

    def load_data(self):
        self.data = pd.read_csv(self.data_path)
        print("Data loaded successfully.")

    def preprocess_data(self):
        # Assuming specific processing based on your data structure
        self.data['Has_Bachelor'] = self.data['Education'].str.contains('Bachelor', na=False).astype(int)
        self.data['Has_Master'] = self.data['Education'].str.contains('Master', na=False).astype(int)
        self.data['Has_Doctorate'] = self.data['Education'].str.contains('Doctorate', na=False).astype(int)
        print("Data preprocessing complete.")

    def split_data(self):
        features = ['Has_Bachelor', 'Has_Master', 'Has_Doctorate']  # Example features
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.data[features], self.data['Employability'], test_size=0.2, random_state=42)
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)
        print("Data split into train and test sets.")

    def train_model(self):
        params = {
            'C': [0.01, 0.1, 1, 10],
            'penalty': ['l1', 'l2'],
            'solver': ['liblinear']  # 'liblinear' works well with l1 penalty
        }
        grid_search = GridSearchCV(LogisticRegression(), params, cv=5, scoring='accuracy')
        grid_search.fit(self.X_train, self.y_train)
        self.model = grid_search.best_estimator_
        print(f"Model training complete. Best parameters: {grid_search.best_params_}")

    def evaluate_model(self):
        y_pred = self.model.predict(self.X_test)
        accuracy = accuracy_score(self.y_test, y_pred)
        print(f"Model accuracy: {accuracy}")

    def save_model(self, path='model.joblib'):
        joblib.dump(self.model, path)
        print("Model saved to", path)

    def load_model(self, path='model.joblib'):
        self.model = joblib.load(path)
        print("Model loaded from", path)

    def full_pipeline(self):
        self.load_data()
        self.preprocess_data()
        self.split_data()
        self.train_model()
        self.evaluate_model()

# Usage example
# predictor = EmploymentPredictor(data_path="indeed_raw_datas.csv")
# predictor.full_pipeline()
# predictor.save_model()

