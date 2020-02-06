# -*- coding: utf-8 -*-
"""
    pvsyst.model
    ~~~~~
    
    
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd
import concurrent.futures as futures

from pvlib.modelchain import ModelChain
from core import Model


class OpticalModel(Model):

    def __init__(self, system, configs, **kwargs):
        super().__init__(system, configs, **kwargs)
        self._components = list()
        for component in system.values():
            if component.type == 'pv':
                model = ModelChain(component, system.location, **dict(configs.items('Model')), **kwargs)
                
                self._components.append(model)

    def run(self, weather, **_):
        # FIXME: Look into worse results for split weather
        split = 1 #os.cpu_count() or 1
        
        models = dict()
        components = dict()
        with futures.ThreadPoolExecutor(max_workers=split) as executor:
            weather_days = list(dict(tuple(weather.groupby(weather.index.date))).values())
            for weather_range in np.array_split(range(0, len(weather_days)), split):
                weather_split = pd.concat(weather_days[weather_range[0]:weather_range[-1]])
                
                for model in self._components:
                    models[executor.submit(model.run_model, weather_split)] = model
            
            for future in futures.as_completed(models):
                model = models[future]
                result = model.ac
                if model.system.id not in components:
                    components[model.system.id] = list()
                
                components[model.system.id].append(result);
        
        results = list()
        for result in components.values():
            results.append(pd.concat(result, axis=0))
        
        return pd.DataFrame(pd.concat(results, axis=1).sum(axis=1), columns=['p_mp'])

