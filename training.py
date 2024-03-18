import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

data = pd.read_csv('cesu_17below.csv')

# Define custom encoding dictionaries for each categorical column
encoding_dict_kasarian = {'Lalake': 0, 'Babae': 1}
encoding_dict_edad= {'17-below': 0, '18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4, '55-64': 5, '65-Above': 6 }
encoding_dict_antas = {'Hindi nakapagtapos ng Elementarya':0, 'Elementarya':1, 'Hindi nakapagtapos ng Sekundarya':2, 'Sekundarya':3, 'Kolehiyo':4, 'Hindi nakapagtapos ng Kolehiyo':5, 'Masters Degree':6, 'Doctorate Degree':7, 'Hindi nakapag-aral':8}  # Define your categories and values
encoding_dict_uri = {'May Trabaho': 1, 'Walang Trabaho': 0}  # Define your categories and values
#encoding_dict_program = {'Literacy': 0, 'Socio-economic': 1, 'Environmental Stewardship': 2, 'Health and Wellness': 3, 'Cultural Enhancement': 4, 'Values Formation': 5, 'Disaster Management': 6, 'Gender and Development': 7}  # Define your categories and values

# Apply custom encoding to the categorical columns
data['Kasarian'] = data['Kasarian'].map(encoding_dict_kasarian)
data['Edad'] = data['Edad'].map(encoding_dict_edad)
data['Antas na tinapos'] = data['Antas na tinapos'].map(encoding_dict_antas)
data['Uri ng trabaho'] = data['Uri ng trabaho'].map(encoding_dict_uri)
#data['Program'] = data['Program'].map(encoding_dict_program)

# Split the data into training and testing sets
X = data.drop(['Program'], axis=1)  # Features
y = data['Program']  # Target variable

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

rfc = RandomForestClassifier(n_estimators=100, random_state=42)

rfc.fit(X_train, y_train)

y_pred = rfc.predict(X_test)

# Check accuracy score
accuracy = accuracy_score(y_test, y_pred)
print('Model accuracy score with 100 decision-trees: {0:0.4f}'.format(accuracy))

# Assuming 'rfc' is your trained Random Forest Classifier
joblib.dump(rfc, 'trained_modelCESU7.pkl')