import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Load the CSV data
data2 = pd.read_csv('cesu17-below_subprogram_May_Trabaho.csv')
df2 = pd.DataFrame(data2)
# Define custom encoding dictionaries for each categorical column
encoding_dict_kasarian = {'Lalake': 0, 'Babae': 1}
encoding_dict_edad= {'17-below': 0, '18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4, '55-64': 5, '65-Above': 6 }
encoding_dict_antas = {'Hindi nakapagtapos ng Elementarya':0, 'Elementarya':1, 'Hindi nakapagtapos ng Sekundarya':2, 'Sekundarya':3, 'Kolehiyo':4, 'Hindi nakapagtapos ng Kolehiyo':5, 'Masters Degree':6, 'Doctorate Degree':7, 'Hindi nakapag-aral':8}
encoding_dict_uri = {'May Trabaho': 1, 'Walang Trabaho': 0}
encoding_dict_program = {'Literacy': 0, 'Socio-economic': 1, 'Environmental Stewardship': 2, 'Health and Wellness': 3, 'Cultural Enhancement': 4, 'Values Formation': 5, 'Disaster Management': 6, 'Gender and Development': 7}

# Apply custom encoding to the categorical columns
data2['Kasarian'] = data2['Kasarian'].map(encoding_dict_kasarian)
data2['Edad'] = data2['Edad'].map(encoding_dict_edad)
data2['Antas na tinapos'] = data2['Antas na tinapos'].map(encoding_dict_antas)
data2['Uri ng trabaho'] = data2['Uri ng trabaho'].map(encoding_dict_uri)
data2['Program'] = data2['Program'].map(encoding_dict_program)

# Split the data into training and testing sets
X2 = data2.drop(['Sub Program'], axis=1)  # Features
y2 = data2['Sub Program']  # Target variable

X_train2, X_test2, y_train2, y_test2 = train_test_split(X2, y2, test_size=0.33, random_state=42)


rfc2 = RandomForestClassifier(n_estimators=100, random_state=42)

rfc2.fit(X_train2, y_train2)

y_pred2 = rfc2.predict(X_test2)

# Check accuracy score
accuracy = accuracy_score(y_test2, y_pred2)
print('Model accuracy score with 100 decision-trees: {0:0.4f}'.format(accuracy))


joblib.dump(rfc2, 'subprogram7.pkl')