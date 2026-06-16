from typing import Any

from lumina.graph import ModelGraph, Node, Edge
from lumina.parsers.base import Parser


class SklearnParser(Parser):
    def parse(self, model: Any) -> ModelGraph:
        from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

        if isinstance(model, (DecisionTreeClassifier, DecisionTreeRegressor)):
            return self._parse_decision_tree(model)

        return self._parse_simple_estimator(model)

    def _parse_decision_tree(self, model: Any) -> ModelGraph:
        tree = model.tree_
        nodes = []
        edges = []

        feature_names = getattr(model, "feature_names_in_", None)
        class_names = getattr(model, "classes_", None)

        for idx in range(tree.node_count):
            is_leaf = tree.children_left[idx] == tree.children_right[idx]
            if is_leaf:
                value = tree.value[idx]
                if class_names is not None and len(class_names) == value.shape[1]:
                    label = self._leaf_label(value, class_names)
                else:
                    label = f"value={value.squeeze().round(3)}"
                display = f"leaf: {label}"
                node_type = "Leaf"
                params = {"value": value.tolist(), "samples": int(tree.n_node_samples[idx])}
            else:
                feat_idx = int(tree.feature[idx])
                feat_name = f"feature_{feat_idx}" if feature_names is None else str(feature_names[feat_idx])
                threshold = round(float(tree.threshold[idx]), 4)
                display = f"{feat_name} <= {threshold}"
                node_type = "Decision"
                params = {
                    "feature": feat_name,
                    "threshold": threshold,
                    "samples": int(tree.n_node_samples[idx]),
                    "impurity": round(float(tree.impurity[idx]), 4),
                }

            nodes.append(Node(id=str(idx), type=node_type, params=params, display_name=display))

            left = tree.children_left[idx]
            right = tree.children_right[idx]
            if left != right:
                edges.append(Edge(source=str(idx), target=str(left)))
                edges.append(Edge(source=str(idx), target=str(right)))

        return ModelGraph(
            nodes=nodes,
            edges=edges,
            metadata={"framework": "sklearn", "estimator": model.__class__.__name__},
        )

    def _parse_simple_estimator(self, model: Any) -> ModelGraph:
        node = Node(
            id="0",
            type=model.__class__.__name__,
            params={},
            display_name=f"0 ({model.__class__.__name__})",
        )
        return ModelGraph(nodes=[node], edges=[], metadata={"framework": "sklearn"})

    def _leaf_label(self, value: Any, class_names: Any) -> str:
        class_index = int(value.argmax(axis=1)[0])
        return str(class_names[class_index])
