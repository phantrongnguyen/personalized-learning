from __future__ import annotations

import time
import numpy as np
from .evaluation import group_cv_score

def fitness(metric, selected, total, alpha):
    if not 0 <= alpha <= 1: raise ValueError('alpha must be between 0 and 1')
    return float(alpha*metric + (1-alpha)*(1-selected/total))

class MaskObjective:
    def __init__(self, frame, y, groups, config, alpha=0.85):
        self.frame=frame; self.y=np.asarray(y); self.groups=np.asarray(groups); self.config=config; self.alpha=alpha; self.cache={}; self.calls=0; self.cache_hits=0
    def __call__(self, mask):
        key=tuple(np.asarray(mask,dtype=np.int8));
        if key in self.cache: self.cache_hits += 1; return self.cache[key]
        chosen=np.flatnonzero(mask)
        if not len(chosen): return (0.0,0.0)
        metric=group_cv_score(self.frame,self.y,self.groups,self.config,self.frame.columns[chosen].tolist())
        result=(fitness(metric,len(chosen),len(mask),self.alpha),metric); self.cache[key]=result; self.calls+=1; return result

def random_mask(rng,n):
    mask=rng.integers(0,2,size=n,dtype=np.int8)
    if not mask.any(): mask[rng.integers(0,n)]=1
    return mask

def local_search(objective, start, seed=42, max_steps=20):
    rng=np.random.default_rng(seed); best=start.copy(); best_fit=objective(best)[0]; history=[best_fit]
    for _ in range(max_steps):
        candidate=best.copy(); i=rng.integers(0,len(candidate)); candidate[i]=1-candidate[i]
        if not candidate.any(): continue
        value=objective(candidate)[0]
        if value>best_fit: best,best_fit=candidate,value
        history.append(best_fit)
    return best,best_fit,history

def run_search(method, objective, seed=42, population=4, iterations=3):
    started=time.perf_counter(); rng=np.random.default_rng(seed); n=objective.frame.shape[1]
    if method == 'VNLS':
        best, fit_value, history = local_search(objective, random_mask(rng,n), seed, 20)
    else:
        positions=rng.uniform(-2,2,size=(population,n)); velocities=rng.uniform(-0.5,0.5,size=(population,n))
        masks=(rng.random((population,n)) < (1/(1+np.exp(-positions)))).astype(np.int8)
        masks[np.sum(masks,axis=1)==0, rng.integers(0,n)] = 1
        best=masks[0].copy(); fit_value=-1; history=[]
        for iteration in range(iterations):
            for mask in masks:
                value=objective(mask)[0]
                if value>fit_value: best,fit_value=mask.copy(),value
            if method == 'HCO-VNLS':
                best,fit_value,local_history=local_search(objective,best,seed+iteration,5)
                history.extend(local_history)
            else:
                history.append(fit_value)
            inertia=0.9-0.5*(iteration/max(iterations,1))
            for index in range(population):
                r1=rng.random(n); r2=rng.random(n); neighbor=masks[rng.integers(0,population)]
                velocities[index]=inertia*velocities[index]+1.4*r1*(best-positions[index])+1.1*r2*(neighbor-positions[index])
                positions[index]=positions[index]+np.clip(velocities[index],-2,2)
                masks[index]=(rng.random(n) < (1/(1+np.exp(-np.clip(positions[index],-12,12))))).astype(np.int8)
                if not masks[index].any(): masks[index,rng.integers(0,n)]=1
    metric=objective(best)[1]
    return {'method':method,'seed':seed,'selected_count':int(best.sum()),'fitness_cv':float(fit_value),'average_precision_cv':float(metric),'objective_calls':objective.calls,'cache_hits':objective.cache_hits,'wall_seconds':time.perf_counter()-started,'history':history,'selected_columns':objective.frame.columns[np.flatnonzero(best)].tolist()}


def run_search_budgeted(method, objective, seed=42, budget=24, population=4):
    """Run comparable binary search methods with the same uncached objective budget."""
    started = time.perf_counter()
    rng = np.random.default_rng(seed)
    n = objective.frame.shape[1]
    history = []
    if method == "VNLS":
        best = random_mask(rng, n)
        best_fit = objective(best)[0]
        history.append(best_fit)
        attempts = 0
        while objective.calls < budget and attempts < budget * 3:
            candidate = best.copy()
            candidate[rng.integers(0, n)] ^= 1
            if not candidate.any():
                attempts += 1
                continue
            value = objective(candidate)[0]
            if value > best_fit:
                best, best_fit = candidate, value
            history.append(best_fit)
            attempts += 1
    else:
        positions = rng.uniform(-2, 2, size=(population, n))
        velocities = rng.uniform(-0.5, 0.5, size=(population, n))
        masks = (rng.random((population, n)) < (1 / (1 + np.exp(-positions)))).astype(np.int8)
        for row in range(population):
            if not masks[row].any():
                masks[row, rng.integers(0, n)] = 1
        best = masks[0].copy()
        best_fit = -1.0
        iteration = 0
        while objective.calls < budget and iteration < budget * 2:
            for mask in masks:
                if objective.calls >= budget:
                    break
                value = objective(mask)[0]
                if value > best_fit:
                    best, best_fit = mask.copy(), value
            history.append(best_fit)
            if method == "HCO-VNLS" and objective.calls < budget:
                remaining = max(1, min(5, budget - objective.calls))
                best, best_fit, local_history = local_search(objective, best, seed + iteration, remaining)
                history.extend(local_history)
            inertia = 0.9 - 0.5 * (iteration / max(iteration + 1, 1))
            for row in range(population):
                r1 = rng.random(n); r2 = rng.random(n)
                neighbor = masks[rng.integers(0, population)]
                velocities[row] = inertia * velocities[row] + 1.4 * r1 * (best - positions[row]) + 1.1 * r2 * (neighbor - positions[row])
                positions[row] = positions[row] + np.clip(velocities[row], -2, 2)
                masks[row] = (rng.random(n) < (1 / (1 + np.exp(-np.clip(positions[row], -12, 12))))).astype(np.int8)
                if not masks[row].any():
                    masks[row, rng.integers(0, n)] = 1
            iteration += 1
    metric = objective(best)[1]
    return {"method": method, "seed": seed, "budget": budget, "selected_count": int(best.sum()), "fitness_cv": float(best_fit), "average_precision_cv": float(metric), "objective_calls": objective.calls, "cache_hits": objective.cache_hits, "wall_seconds": time.perf_counter() - started, "history": history, "selected_columns": objective.frame.columns[np.flatnonzero(best)].tolist()}
