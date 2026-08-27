"""
Module: Variable Neighborhood Local Search (VNLS) for Feature Selection
Author: KLTN 13 - HUIT
Reference: Hansen, P., Mladenovic, N., et al. (2017). Variable neighborhood search: basics and variants.
"""

from typing import Tuple, List, Callable
import numpy as np


class VariableNeighborhoodLocalSearch:
    """
    VNLS local optimizer using k-flip and swap neighborhood structures.
    """
    def __init__(self, k_max: int = 4, max_local_steps: int = 8, random_state: int = 42):
        self.k_max = k_max
        self.max_local_steps = max_local_steps
        self.random_state = random_state
        np.random.seed(self.random_state)

    def _generate_neighbor(self, solution: np.ndarray, neighborhood_type: int) -> np.ndarray:
        """
        Generates candidate solution using neighborhood structure k:
        k = 1: 1-bit flip
        k = 2: 2-bit flip
        k = 3: Bit swap (1 with 0)
        k = 4: Random feature drop (1 -> 0)
        """
        candidate = solution.copy()
        n_features = len(candidate)

        if neighborhood_type == 1:
            # 1-bit flip
            idx = np.random.randint(n_features)
            candidate[idx] = 1 - candidate[idx]

        elif neighborhood_type == 2:
            # 2-bit flip
            indices = np.random.choice(n_features, size=min(2, n_features), replace=False)
            candidate[indices] = 1 - candidate[indices]

        elif neighborhood_type == 3:
            # Bit swap: swap one active feature with one inactive feature
            ones = np.where(candidate == 1)[0]
            zeros = np.where(candidate == 0)[0]
            if len(ones) > 0 and len(zeros) > 0:
                o_idx = np.random.choice(ones)
                z_idx = np.random.choice(zeros)
                candidate[o_idx] = 0
                candidate[z_idx] = 1

        elif neighborhood_type >= 4:
            # Feature reduction perturbation
            ones = np.where(candidate == 1)[0]
            if len(ones) > 1:
                drop_idx = np.random.choice(ones)
                candidate[drop_idx] = 0

        # Safety check: ensure at least one bit is set
        if np.sum(candidate) == 0:
            candidate[np.random.randint(n_features)] = 1

        return candidate

    def search(
        self,
        solution: np.ndarray,
        current_fitness: float,
        evaluate_fn: Callable[[np.ndarray], Tuple[float, float]]
    ) -> Tuple[np.ndarray, float]:
        """
        Executes Variable Neighborhood Local Search on the given solution.
        """
        best_sol = solution.copy()
        best_fit = current_fitness

        k = 1
        while k <= self.k_max:
            improved = False
            for _ in range(self.max_local_steps):
                candidate = self._generate_neighbor(best_sol, neighborhood_type=k)
                cand_fit, _ = evaluate_fn(candidate)

                if cand_fit > best_fit:
                    best_sol = candidate
                    best_fit = cand_fit
                    improved = True
                    # Re-center search and restart from k=1
                    k = 1
                    break

            if not improved:
                k += 1  # Move to next larger neighborhood structure

        return best_sol, best_fit
