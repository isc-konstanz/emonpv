from collections import OrderedDict
from functools import partial
from pvlib import modelchain
import pandas as pd
import numpy as np


class ModelChain(modelchain.ModelChain):
    """
    An experimental class that represents all of the modeling steps
    necessary for calculating power or energy for a PV system at a given
    location using the SAPM.

    CEC module specifications and the single diode model are not yet
    supported.

    Parameters
    ----------
    system : PVSystem
        A :py:class:`~pvlib.pvsystem.PVSystem` object that represents
        the connected set of modules, inverters, etc.

    location : Location
        A :py:class:`~pvlib.location.Location` object that represents
        the physical location at which to evaluate the model.

    orientation_strategy : None or str, default 'south_at_latitude_tilt'
        The strategy for aligning the modules. If not None, sets the
        ``surface_azimuth`` and ``surface_tilt`` properties of the
        ``system``. Allowed strategies include 'flat',
        'south_at_latitude_tilt'. Ignored for SingleAxisTracker systems.

    clearsky_model : str, default 'ineichen'
        Passed to location.get_clearsky.

    transposition_model : str, default 'haydavies'
        Passed to system.get_irradiance.

    solar_position_method : str, default 'nrel_numpy'
        Passed to location.get_solarposition.

    airmass_model : str, default 'kastenyoung1989'
        Passed to location.get_airmass.

    dc_model: None, str, or function, default None
        If None, the model will be inferred from the contents of
        system.module_parameters. Valid strings are 'sapm',
        'singlediode', 'pvwatts'. The ModelChain instance will be passed
        as the first argument to a user-defined function.

    ac_model: None, str, or function, default None
        If None, the model will be inferred from the contents of
        system.inverter_parameters and system.module_parameters. Valid
        strings are 'snlinverter', 'adrinverter' (not implemented),
        'pvwatts'. The ModelChain instance will be passed as the first
        argument to a user-defined function.

    aoi_model: None, str, or function, default None
        If None, the model will be inferred from the contents of
        system.module_parameters. Valid strings are 'physical',
        'ashrae', 'sapm', 'no_loss'. The ModelChain instance will be
        passed as the first argument to a user-defined function.

    spectral_model: None, str, or function, default None
        If None, the model will be inferred from the contents of
        system.module_parameters. Valid strings are 'sapm',
        'first_solar' (not implemented), 'no_loss'. The ModelChain
        instance will be passed as the first argument to a user-defined
        function.

    temp_model: str or function, default 'sapm'
        Valid strings are 'sapm'. The ModelChain instance will be passed
        as the first argument to a user-defined function.

    losses_model: str or function, default 'no_loss'
        Valid strings are 'pvwatts', 'no_loss'. The ModelChain instance
        will be passed as the first argument to a user-defined function.

    name: None or str, default None
        Name of ModelChain instance.

    **kwargs
        Arbitrary keyword arguments. Included for compatibility, but not
        used.
    """

    def infer_aoi_model(self):
        params = set(self.system.module_parameters.keys())
        if set(['K', 'L', 'n']) <= params:
            return self.physical_aoi_loss
        elif set(['B5', 'B4', 'B3', 'B2', 'B1', 'B0']) <= params:
            return self.sapm_aoi_loss
        elif set(['b']) <= params:
            return self.ashrae_aoi_loss
        else:
            #return self.no_aoi_loss
            return self.physical_aoi_loss
    
    def infer_spectral_model(self):
        params = set(self.system.module_parameters.keys())
        if set(['A4', 'A3', 'A2', 'A1', 'A0']) <= params:
            return self.sapm_spectral_loss
        else:
            return self.no_spectral_loss
    
    @property
    def dc_model(self):
        return self._dc_model

    @dc_model.setter
    def dc_model(self, model):
        if model is None:
            self._dc_model = self.infer_dc_model()
        elif isinstance(model, str):
            model = model.lower()
            if model == 'sapm':
                self._dc_model = self.sapm
            elif model == 'singlediode':
                self._dc_model = self.singlediode
            elif model == 'pvwatts':
                self._dc_model = self.pvwatts_dc
            elif model == 'basic':
                self._dc_model = self.basic
            else:
                raise ValueError(model + ' is not a valid DC power model')
        else:
            self._dc_model = partial(model, self)

    def infer_dc_model(self):
        params = set(self.system.module_parameters.keys())
        if set(['A0', 'A1', 'C7']) <= params:
            return self.sapm
        elif set(['a_ref', 'I_L_ref', 'I_o_ref', 'R_sh_ref', 'R_s']) <= params:
            return self.singlediode
        elif set(['pdc0', 'gamma_pdc']) <= params:
            return self.pvwatts_dc
        else:
            return self.basic

    def basic(self):
        module = self.system.module_parameters
        effective_irradiance = self.effective_irradiance/1000.
        T0 = 25
        eta = 0.825

        v_mp = module['V_mp_ref']
        i_mp = module['I_mp_ref']
        out = OrderedDict()
        out['v_mp'] = np.maximum(0, (v_mp + np.log(effective_irradiance)))#*module['N_s'])???
        out['p_mp'] = v_mp * i_mp*effective_irradiance*(1 + module['gamma_r']/100*(self.temps['temp_cell'] - T0))*module['N_s']*eta
        if isinstance(out['p_mp'], pd.Series):
            out = pd.DataFrame(out)
        self.dc = out
        return self

    def singlediode(self):
        self.system.module_parameters['EgRef'] = 1.121
        self.system.module_parameters['dEgdT'] = -0.0002677
        
        (photocurrent, saturation_current, resistance_series,
         resistance_shunt, nNsVth) = (
            self.system.calcparams_desoto(self.effective_irradiance,
                                          self.temps['temp_cell']))

        self.desoto = (photocurrent, saturation_current, resistance_series,
                       resistance_shunt, nNsVth)

        self.dc = self.system.singlediode(
            photocurrent, saturation_current, resistance_series,
            resistance_shunt, nNsVth)
        self.dc = self.system.scale_voltage_current_power(self.dc).fillna(0)

        return self