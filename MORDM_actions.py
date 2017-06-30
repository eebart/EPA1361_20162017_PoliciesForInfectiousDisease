# Import things from EMA Workbench

from ema_workbench import Policy, Scenario, perform_experiments
from ema_workbench import (RealParameter, CategoricalParameter, Constant,
                          ScalarOutcome)
from ema_workbench.connectors.vensim import VensimModel
from ema_workbench.em_framework.outcomes import AbstractOutcome
from ema_workbench.em_framework.samplers import sample_uncertainties
from ema_workbench.em_framework.evaluators import LHS, SequentialEvaluator

from ema_workbench import save_results
from ema_workbench import ema_logging

from platypus import Problem, unique, nondominated, Real, EpsNSGAII
import functools
import pandas as pd
import numpy as np
import sys

ema_logging.log_to_stderr(ema_logging.INFO)

if __name__ == '__main__':

    infection = sys.argv[1]
    dying = sys.argv[2]

    infection_buckets = {
        'low': [0.5, 1.9],
        'high': [1.9, 5],
        'all': [0.5, 5]
    }

    dying_buckets = {
        'low': [0.1, 0.15],
        'high': [0.15, 0.5],
        'all': [0.1, 0.5]
    }

    infection_bucket = infection_buckets[infection.lower()]
    dying_bucket = dying_buckets[dying.lower()]

#We can define common uncertainties and outcomes for each model:
uncertainties = [RealParameter('Average incubation time', 0.5, 14),
                 RealParameter('Average infectious period', 7, 21),
                 RealParameter('Basic reproduction number', infection_bucket[0], infection_bucket[1]),
                 RealParameter('Case fatality rate', dying_bucket[0], dying_bucket[1]),
                 CategoricalParameter('Switch SEIR or SIR', [1,0]),

                 RealParameter('Base Transmission Coefficient Social Distance III', 0.7, 0.8),
                 RealParameter('Base Societal Stress Coefficient Social Distance III', 0.5, 0.9),
                 RealParameter('Base Effort Coefficient Social Distance III', 4, 8),
                 RealParameter('Implementation Time Social Distance III', 2, 4),
                 RealParameter('Duration Social Distance III', 5, 21),

                 RealParameter('Base Transmission Coefficient Social Distance II', 0.89, 0.96),
                 RealParameter('Base Societal Stress Coefficient Social Distance II', 0.3, 0.8),
                 RealParameter('Base Effort Coefficient Social Distance II', 3, 6),
                 RealParameter('Implementation Time Social Distance II', 1, 3),
                 RealParameter('Duration Social Distance II', 5, 21),

                 RealParameter('Base Transmission Coefficient Social Distance I', 0.92, 0.97),
                 RealParameter('Base Societal Stress Coefficient Social Distance I', 0.2, 0.3),
                 RealParameter('Base Effort Coefficient Social Distance I', 2, 3),
                 RealParameter('Implementation Time Social Distance I', 1, 3),
                 RealParameter('Duration Social Distance I', 7, 90),

                 RealParameter('Base Transmission Coefficient Public Info', 0.97, 0.99),
                 RealParameter('Base Societal Stress Coefficient Public Info', 0.01, 0.1),
                 RealParameter('Base Effort Coefficient Public Info', 1, 2),
                 RealParameter('Implementation Time Public Info', 2, 5),
                 RealParameter('Duration Public Info', 7, 28),

                 RealParameter('Base Transmission Coefficient Public Edu', 0.97, 0.99),
                 RealParameter('Base Societal Stress Coefficient Public Edu', 0.01, 0.1),
                 RealParameter('Base Effort Coefficient Public Edu', 1, 2),
                 RealParameter('Implementation Time Public Edu', 2, 5),
                 RealParameter('Duration Public Edu', 7,28),

                 RealParameter('Base Transmission Coefficient Facemasks', 0.93, 0.97),
                 RealParameter('Base Societal Stress Coefficient Facemasks', 0.1, 0.15),
                 RealParameter('Base Effort Coefficient Facemasks', 2, 3),
                 RealParameter('Implementation Time Facemasks', 5, 10),
                 RealParameter('Duration Facemasks', 7,28),

                 RealParameter('Base Transmission Coefficient Tracing', 0.87, 0.93),
                 RealParameter('Base Societal Stress Coefficient Tracing', 0.1, 0.3),
                 RealParameter('Base Effort Coefficient Tracing', 3, 7),
                 RealParameter('Implementation Time Tracing', 2, 10),
                 RealParameter('Duration Tracing', 7,42),

                 RealParameter('Base Transmission Coefficient Case Isolation', 0.73, 0.87),
                 RealParameter('Base Recovery Coefficient Case Isolation', 0.92, 0.97),
                 RealParameter('Base Societal Stress Coefficient Case Isolation', 0.3, 0.6),
                 RealParameter('Base Effort Coefficient Case Isolation', 5, 9),
                 RealParameter('Implementation Time Case Isolation', 14, 28),
                 RealParameter('Duration Case Isolation', 14, 60),

                 RealParameter('Base Societal Stress Coefficient Involuntary Immunization', 0.5, 0.8),
                 RealParameter('Base Effort Coefficient Involuntary Immunization', 5, 10),
                 RealParameter('Implementation Time Involuntary Immunization', 30, 180),
                 RealParameter('Duration Involuntary Immunization', 7,14),

                 RealParameter('Base Societal Stress Coefficient Voluntary Immunization', 0.1, 0.3),
                 RealParameter('Base Effort Coefficient Voluntary Immunization', 2, 6),
                 RealParameter('Implementation Time Voluntary Immunization', 30, 180),
                 RealParameter('Duration Voluntary Immunization', 14, 60),

                 RealParameter('Base Transmission Coefficient Medical Care I', 0.9, 0.97),
                 RealParameter('Base Recovery Coefficient Medical Care I', 0.97, 1),
                 RealParameter('Base Societal Stress Coefficient Medical Care I', 0.05, 0.1),
                 RealParameter('Base Effort Coefficient Medical Care I', 1, 4),
                 RealParameter('Implementation Time Medical Care I', 5, 20),
                 RealParameter('Duration Medical Care I', 14, 60),

                 RealParameter('Base Transmission Coefficient Medical Care II', 0.83, 0.9),
                 RealParameter('Base Recovery Coefficient Medical Care II', 0.7, 0.98),
                 RealParameter('Base Societal Stress Coefficient Medical Care II', 0.05, 0.1),
                 RealParameter('Base Effort Coefficient Medical Care II', 4, 8),
                 RealParameter('Implementation Time Medical Care II', 20, 40),
                 RealParameter('Duration Medical Care II', 14, 60),
                 ]

outcomes = [ScalarOutcome('Deceased population'),
            ScalarOutcome('Infectious population'),
            ScalarOutcome('Stock Total Effort'),
            ScalarOutcome('Stock Societal Stress')]

robustness = [ScalarOutcome('Deceased population', kind=ScalarOutcome.MINIMIZE, function=np.max),
              ScalarOutcome('Infectious population', kind=ScalarOutcome.MINIMIZE, function=np.mean),
              ScalarOutcome('Stock Total Effort', kind=ScalarOutcome.MINIMIZE, function=np.max),
              ScalarOutcome('Stock Societal Stress', kind=ScalarOutcome.MINIMIZE, function=np.max)]

# Ensure the proper constant values based on information above
constants = [Constant('Initial deceased population', 0),
             Constant('Initial exposed population', 0),
             Constant('Initial infectious population', 1),
             Constant('Initial recovered population', 0),
             Constant('Initial susceptible population', 100000)]

levers = [RealParameter("Lever Social Distance I", 0.00001, 1),
          RealParameter("Lever Social Distance II", 0.00001, 1),
          RealParameter("Lever Social Distance III", 0.00001, 1),
          RealParameter("Lever Public Info", 0.00001, 1),
          RealParameter("Lever Public Edu", 0.00001, 1),
          RealParameter("Lever Facemasks", 0.00001, 1),
          RealParameter("Lever Tracing", 0.00001, 1),
          RealParameter("Lever Case Isolation", 0.00001, 1),
          RealParameter("Lever Voluntary or Involuntary Vaccination", 0.00001, 1),
          RealParameter("Lever Vaccination", 0.00001, 1),
          RealParameter("Lever Medical Care I", 0.00001, 1),
          RealParameter("Lever Medical Care II", 0.00001, 1)]

mdl = VensimModel('Immunization', model_file = r'./models/03_SEIR_SIR_ActionsAsLevers.vpm')
mdl.uncertainties = uncertainties
mdl.outcomes = outcomes
mdl.constants = constants
mdl.levers = levers
mdl.robustness = robustness
mdl.time_horizon = 360

n_scenarios = 50
scenarios = sample_uncertainties(mdl, n_scenarios)
nfe = 1000

with SequentialEvaluator(mdl) as evaluator:
    robust_results = evaluator.robust_optimize(mdl.robustness, scenarios, nfe=nfe,
                                  epsilons=[0.1,]*len(mdl.robustness), population_size=25)

output_file = './platypus_results/' + infection + 'I_' + dying + 'D.csv'
robust_results.to_csv(output_file)
