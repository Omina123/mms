from sklearn.preprocessing import LabelEncoder

categorical_feature = ['cat', 'dog', 'dog', 'cat', 'bird']

encoder = LabelEncoder()

encoded_feature = encoder.fit_transform(categorical_feature)

print("Encoded feature:", encoded_feature)