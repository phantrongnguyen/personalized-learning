"""
Module: Optimization Baseline Algorithms (GA & PSO) for Feature Selection
Author: KLTN 13 - HUIT
"""

import warnings
warnings.filterwarnings("ignore")

from typing import Tuple, List, Optional, Any
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier

from .hco import sigmoid


class GeneticAlgorithm:
    """
    Standard Genetic Algorithm (GA) for Binary Feature Selection.
    """
    def __init__(
        self,
        pop_size: int = 25,
        max_iter: int = 30,
        alpha: float = 0.85,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.05,
        eval_estimator: Optional[Any] = None,
        random_state: int = 42
    ):
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.alpha = alpha
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.eval_estimator = eval_estimator
        self.random_state = random_state

        self.best_solution: Optional[np.ndarray] = None
        self.best_fitness: float = float("-inf")
        self.history: List[float] = []
        np.random.seed(self.random_state)

    def _get_estimator(self):
        if self.eval_estimator is not None:
            return self.eval_estimator
        return DecisionTreeClassifier(max_depth=5, random_state=self.random_state)

    def evaluate_fitness(self, binary_mask: np.ndarray, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
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
        num_features = X.shape[1]
        population = np.random.randint(0, 2, size=(self.pop_size, num_features))
        for i in range(self.pop_size):
            if np.sum(population[i]) == 0:
                population[i, np.random.randint(num_features)] = 1

        self.history = []
        self.best_fitness = float("-inf")
        self.best_solution = None

        for _ in range(self.max_iter):
            fitness_scores = np.zeros(self.pop_size)
            for i in range(self.pop_size):
                fit, _ = self.evaluate_fitness(population[i], X, y)
                fitness_scores[i] = fit
                if fit > self.best_fitness:
                    self.best_fitness = fit
                    self.best_solution = population[i].copy()

            self.history.append(self.best_fitness)

            # Roulette wheel selection
            prob_weights = np.maximum(fitness_scores, 1e-4)
            prob_weights /= np.sum(prob_weights)
            selected_idx = np.random.choice(self.pop_size, size=self.pop_size, p=prob_weights)
            new_pop = population[selected_idx].copy()

            # Single-point crossover
            for i in range(0, self.pop_size - 1, 2):
                if np.random.rand() < self.crossover_rate:
                    point = np.random.randint(1, num_features)
                    new_pop[i, point:], new_pop[i + 1, point:] = (
                        population[i + 1, point:].copy(),
                        population[i, point:].copy(),
                    )

            # Mutation
            mutation_mask = np.random.rand(*new_pop.shape) < self.mutation_rate
            new_pop = np.where(mutation_mask, 1 - new_pop, new_pop)

            for i in range(self.pop_size):
                if np.sum(new_pop[i]) == 0:
                    new_pop[i, np.random.randint(num_features)] = 1

            population = new_pop

        return self.best_solution, self.best_fitness, self.history


class ParticleSwarmOptimization:
    """
    Binary Particle Swarm Optimization (BPSO) for Feature Selection.
    """
    def __init__(
        self,
        pop_size: int = 25,
        max_iter: int = 30,
        alpha: float = 0.85,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        eval_estimator: Optional[Any] = None,
        random_state: int = 42
    ):
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.alpha = alpha
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.eval_estimator = eval_estimator
        self.random_state = random_state

        self.best_solution: Optional[np.ndarray] = None
        self.best_fitness: float = float("-inf")
        self.history: List[float] = []
        np.random.seed(self.random_state)

    def _get_estimator(self):
        if self.eval_estimator is not None:
            return self.eval_estimator
        return DecisionTreeClassifier(max_depth=5, random_state=self.random_state)

    def evaluate_fitness(self, binary_mask: np.ndarray, X: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
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
        num_features = X.shape[1]
        positions = np.random.uniform(-3, 3, size=(self.pop_size, num_features))
        velocities = np.random.uniform(-1, 1, size=(self.pop_size, num_features))

        pbest_pos = positions.copy()
        pbest_fit = np.full(self.pop_size, float("-inf"))

        self.best_fitness = float("-inf")
        self.best_solution = None
        self.history = []

        for _ in range(self.max_iter):
            binary_pop = np.where(np.random.rand(self.pop_size, num_features) < sigmoid(positions), 1, 0)
            for i in range(self.pop_size):
                if np.sum(binary_pop[i]) == 0:
                    binary_pop[i, np.random.randint(num_features)] = 1

                fit, _ = self.evaluate_fitness(binary_pop[i], X, y)
                if fit > pbest_fit[i]:
                    pbest_fit[i] = fit
                    pbest_pos[i] = positions[i].copy()

                if fit > self.best_fitness:
                    self.best_fitness = fit
                    self.best_solution = binary_pop[i].copy()

            self.history.append(self.best_fitness)

            # Velocity and position updates
            for i in range(self.pop_size):
                r1 = np.random.rand(num_features)
                r2 = np.random.rand(num_features)
                gbest_pos = np.where(self.best_solution == 1, 2.0, -2.0)

                velocities[i] = (
                    self.w * velocities[i]
                    + self.c1 * r1 * (pbest_pos[i] - positions[i])
                    + self.c2 * r2 * (gbest_pos - positions[i])
                )
                velocities[i] = np.clip(velocities[i], -3, 3)
                positions[i] += velocities[i]

        return self.best_solution, self.best_fitness, self.history
