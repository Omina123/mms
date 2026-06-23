# # import matplotlib.pyplot as plt 
# # x = [10, 20, 30, 40, 50]
# # y = [20,25, 35, 45, 55]
# # plt.plot(x, y)
# # plt.title("SAMPLE PLOT")
# # plt .ylabel("Y-AXIS")
# # plt.xlabel("X-AXIS")
# # plt.show()
# import matplotlib.pyplot as plt
# import pandas as pd
# cars = ['BMW', 'AUDI', 'TOYOTA', 'HONDA', 'FORD']
# data = [23, 17, 35, 29, 12]
# plt.pie(data, labels=cars, autopct='%1.1f%%', startangle=90)
# plt.title("CAR SALES")
# plt.show()
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
iris=load_iris()
x=iris.data
y= iris.target
features_name = iris.feature_names
target_name = iris.target_names

print(f"feature name is :{features_name} and target name are \n\n\n{target_name} and the types are \n\n\n{type(x)}, and the first 5 are \n\n\n{x[:5]}" )
X_train, X_test, y_train,y_test = train_test_split(x,y, test_size=0.2, random_state=42)