"""
Module: Hybrid HCO-VNLS Algorithm
Author: KLTN 13 - HUIT
Description: Integrates Human Conception Optimizer (Exploration) with Variable Neighborhood Local Search (Exploitation)
"""

import warnings
warnings.filterwarnings("ignore")

from typing import Tuple, List, Optional, Any
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier

from .hco import sigmoid
from .vnls import VariableNeighborhoodLocalSearch


class HCOVNLS:
    """
    Hybrid Human Conception Optimizer with Variable Neighborhood Local Search (HCO-VNLS)
    for optimal feature selection in personalized learning recommendation.
    """
    def __init__(
        self,
        pop_size: int = 25,
        max_iter: int = 30,
        alpha: float = 0.85,
        w_max: float = 0.9,
        w_min: float = 0.4,
        c1: float = 2.0,
        c2: float = 1.5,
        k_max_vnls: int = 4,
        vnls_interval: int = 2,
        eval_estimator: Optional[Any] = None,
        random_state: int = 42
    ):
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.alpha = alpha
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.k_max_vnls = k_max_vnls
        self.vnls_interval = vnls_interval
        self.eval_estimator = eval_estimator
        self.random_state = random_state

        self.vnls = VariableNeighborhoodLocalSearch(k_max=self.k_max_vnls, random_state=self.random_state)
        self.best_solution: Optional[np.ndarray] = None
        self.best_fitness: float = float("-inf")
        self.best_metric_score: float = 0.0
        self.history: List[float] = []

        np.random.seed(self.random_state)

    def _get_estimator(self):
        if self.eval_estimator is not None:
            return self.eval_estimator
        return DecisionTreeClassifier(max_depth=5, random_state=self.random_state)

    def evaluate_fitness(self, binary_mask: np.ndarray, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """
        Calculates fitness score:
        Fitness = alpha * F1_Score + (1 - alpha) * (1 - (selected_features / total_features))
        """
        selected_indices = np.where(binary_mask == 1)[0]
        total_features = len(binary_mask)

        if len(selected_indices) == 0:
            return 0.0, 0.0

        X_sub = X[:, selected_indices]
        estimator = self._get_estimator()

        try:
            scores = cross_val_score(estimator, X_sub, y, cv=3, scoring="f1_weighted", n_jobs=1)
            metric_score = float(np.mean(scores))
        except Exception:
            metric_score = 0.0

        feature_ratio = len(selected_indices) / total_features
        fitness = self.alpha * metric_score + (1.0 - self.alpha) * (1.0 - feature_ratio)
        return fitness, metric_score

    def optimize(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float, List[float]]:
        """
        Runs the hybrid HCO-VNLS algorithm.
        """
        num_features = X.shape[1]

        positions = np.random.uniform(-3, 3, size=(self.pop_size, num_features))
        velocities = np.random.uniform(-1, 1, size=(self.pop_size, num_features))

        binary_pop = np.where(np.random.rand(self.pop_size, num_features) < sigmoid(positions), 1, 0)
        for i in range(self.pop_size):
            if np.sum(binary_pop[i]) == 0:
                binary_pop[i, np.random.randint(num_features)] = 1

        self.history = []
        self.best_fitness = float("-inf")
        self.best_solution = None

        # Closure for VNLS fitness evaluation
        eval_fn = lambda mask: self.evaluate_fitness(mask, X, y)

        for it in range(self.max_iter):
            w = self.w_max - (self.w_max - self.w_min) * (it / self.max_iter)

            # --- Phase 1: HCO Population Evaluation ---
            for i in range(self.pop_size):
                fit, metric = self.evaluate_fitness(binary_pop[i], X, y)
                if fit > self.best_fitness:
                    self.best_fitness = fit
                    self.best_metric_score = metric
                    self.best_solution = binary_pop[i].copy()

            # --- Phase 2: Variable Neighborhood Local Search (VNLS) ---
            if self.best_solution is not None and (it % self.vnls_interval == 0 or it == self.max_iter - 1):
                refined_sol, refined_fit = self.vnls.search(
                    solution=self.best_solution,
                    current_fitness=self.best_fitness,
                    evaluate_fn=eval_fn
                )
                if refined_fit > self.best_fitness:
                    self.best_solution = refined_sol
                    self.best_fitness = refined_fit
                    _, self.best_metric_score = self.evaluate_fitness(self.best_solution, X, y)

            self.history.append(self.best_fitness)

            # --- Phase 3: HCO Position & Velocity Updates ---
            for i in range(self.pop_size):
                r1 = np.random.rand(num_features)
                r2 = np.random.rand(num_features)
                rand_idx = np.random.randint(self.pop_size)

                velocities[i] = (
                    w * velocities[i]
                    + self.c1 * r1 * (self.best_solution - positions[i])
                    + self.c2 * r2 * (positions[rand_idx] - positions[i])
                )
                velocities[i] = np.clip(velocities[i], -3, 3)
                positions[i] += velocities[i]

                probs = sigmoid(positions[i])
                binary_pop[i] = np.where(np.random.rand(num_features) < probs, 1, 0)
                if np.sum(binary_pop[i]) == 0:
                    binary_pop[i, np.random.randint(num_features)] = 1

        return self.best_solution, self.best_fitness, self.history
