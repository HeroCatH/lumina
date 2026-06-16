import modelview
from sklearn.tree import DecisionTreeClassifier

# Train a tiny decision tree
X = [[0], [1], [2], [3], [4], [5]]
y = [0, 0, 0, 1, 1, 1]
model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(X, y)

if __name__ == "__main__":
    modelview.view(model, port=8080)
