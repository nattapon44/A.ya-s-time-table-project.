########################################################################
import sys
import numpy as np
d = {1:80, 2:270, 3:250, 4:160, 5:180}  # customer demand
M = {1:500, 2:500, 3:500}               # factory capacity
I = [1,2,3,4,5]                         # Customers
J = [1,2,3]                             # Factories
cost = {(1,1):4,    (1,2):6,    (1,3):9,
     (2,1):5,    (2,2):4,    (2,3):7,
     (3,1):6,    (3,2):3,    (3,3):3,
     (4,1):8,    (4,2):5,    (4,3):3,
     (5,1):10,   (5,2):8,    (5,3):4
   }                                    # transportation costs
########################################################################
# !pip install pyomo
from pyomo import environ as pe
# ConcreteModel is model where data values supplied at the time of the model definition. As opposite to AbstractModel where data values are supplied in data file
model = pe.ConcreteModel()
# all iterables are to be converted into Set objects
model.d_cust_demand = pe.Set(initialize = d.keys())
model.M_fact_capacity = pe.Set(initialize = M.keys())
# Parameters
# Cartesian product of two sets creates list of tuples [((i1,j1),v1),((i2,j2),v2),...] !!!
model.transport_cost = pe.Param(
    model.d_cust_demand * model.M_fact_capacity,
    initialize = cost,
    within = pe.NonNegativeReals)
model.cust_demand = pe.Param(model.d_cust_demand, 
    initialize = d,
    within = pe.NonNegativeReals)
model.fact_capacity = pe.Param(model.M_fact_capacity, 
    initialize = M,
    within = pe.NonNegativeReals)
########################################################################
model.x = pe.Var(
    model.d_cust_demand * model.M_fact_capacity,
    domain = pe.NonNegativeReals,
    bounds = (0, max(d.values())))
########################################################################
model.objective = pe.Objective(
    expr = pe.summation(model.transport_cost, model.x),
    sense = pe.minimize)
########################################################################
# Constraints: sum of goods == customer demand
def meet_demand(model, customer):
    sum_of_goods_from_factories = sum(model.x[customer,factory] for factory in model.M_fact_capacity)
    customer_demand = model.cust_demand[customer]
    return sum_of_goods_from_factories == customer_demand
model.Constraint1 = pe.Constraint(model.d_cust_demand, rule = meet_demand)
# Constraints: sum of goods <= factory capacity
def meet_capacity(model, factory):
    sum_of_goods_for_customers = sum(model.x[customer,factory] for customer in model.d_cust_demand)
    factory_capacity = model.fact_capacity[factory]
    return sum_of_goods_for_customers <= factory_capacity
model.Constraint2 = pe.Constraint(model.M_fact_capacity, rule = meet_demand)
########################################################################
# !sudo apt-get install glpk-utils
solver = pe.SolverFactory('glpk', executable='/usr/bin/glpsol')
solution = solver.solve(model)
########################################################################
from pyomo.opt import SolverStatus, TerminationCondition
if (solution.solver.status == SolverStatus.ok) and (solution.solver.termination_condition == TerminationCondition.optimal):
    print("Solution is feasible and optimal")
    print("Objective function value = ", model.objective())
elif solution.solver.termination_condition == TerminationCondition.infeasible:
    print ("Failed to find solution.")
else:
    # something else is wrong
    print(str(solution.solver))
assignments = model.x.get_values().items()
EPS = 1.e-6
for (customer,factory),x in sorted(assignments):
    if x > EPS:
        print("sending quantity %10s from factory %3s to customer %3s" % (x, factory, customer))v