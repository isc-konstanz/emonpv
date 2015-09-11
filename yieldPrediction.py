# -*- coding: utf-8 -*-
"""
Created on Thu May 07 14:45:57 2015

@author: Ahmed Mahran
"""

import numpy as np
import pandas as pd
import matplotlib.path as mplPath
import math as m
import pvlib as pv
import fnmatch
import os
import csv
       
h = pd.date_range('20150101', periods= 43800, freq= 'H', tz="Europe/Berlin") #dateTimeIndex used for comparing input data

for file in os.listdir('.'):
    if fnmatch.fnmatch(file, '??_??????????.csv'): 
        fileName = file

rawdata = pd.read_csv(fileName, usecols=['time','aswdifd_s','aswdir_s','t_2m','t_g'])
timeInput = rawdata.time

rawdata['time'] = rawdata['time'].apply(pd.to_datetime)
rawdata.index = pd.to_datetime(rawdata.pop('time'), utc=True)
rawdata.index = rawdata.index.tz_localize('UTC').tz_convert('Europe/Berlin')

sys_par = pd.read_csv('PV_System_Parameters.csv', usecols=['Hco','eta_dirt','eta_field','eta_inv',
                                                           'Umpp0','Impp0','tco_mpp','mow','moh',
                                                           'npar','nser','tilt','panaz','sys_id'])
sys_no = sys_par.panaz[sys_par.panaz > 0].index.size


inputdata = np.zeros((8760,4))
for i in range(len(rawdata)):
    idx = h == rawdata.index[i]
    inputdata[idx,0] = rawdata.aswdifd_s[i]
    inputdata[idx,1] = rawdata.aswdir_s[i]
    inputdata[idx,2] = rawdata.t_2m[i]
    inputdata[idx,3] = rawdata.t_g[i]
for i in range(len(inputdata)):
    if inputdata[i,0] < 0.1:
        inputdata[i,0] = 0
    if inputdata[i,1] < 0.1:
        inputdata[i,1] = 0
dhi = inputdata[:,0]
bhi = inputdata[:,1]
temp = inputdata[:,2]
ghi = bhi + dhi

idx = np.where(inputdata[:,2] > 0.)
idx = idx[0]
idx = idx[0]
     

#location data
longloc = 9.183  #KN
latloc = 47.683

# if Caserta, use these coordinates and comment the previous ones
#longloc = 14.34  #CS from http://dateandtime.info/
#latloc = 41.0761

location = pv.location.Location(latloc, longloc)
sun = pv.solarposition.pyephem(h, location)

### Calculating energy yield from a PV inclined panel
## Step 1: Calculation of solar incidence angle on a fixed tilted surface

#hra = hour angle / ts = solar time / dec = declination angle / 
#doy = day of year / tloc = local time / eot = equation of time [min] / 
#longst = standard reference longitude of local time zone /
#longloc = local longitude / d = time addition (1:in summer, 0:in winter) /
#ele = solar elevation angle / ze = zenith angle / az = solar azimuth angle /
#theta = Solar incidence angle on a fixed tilted surface

Dec = np.empty(0)
I = np.empty(0)
J = np.empty(0)
EoT = np.empty(0)
TS = np.empty(0)
HrA = np.empty(0)
Ele = np.empty(0)
Ze = np.empty(0)
Az = np.empty(0)
Theta = pd.Series()

longst = 15                 #first time zone after UTC
d = 0


tilt = np.empty(0)
panaz = np.empty(0)
Umpp0 = np.empty(0)
Impp0 = np.empty(0)
moh = np.empty(0)
mow = np.empty(0)
npar = np.empty(0)
nser = np.empty(0)
Hco = np.empty(0)
eta_dirt = np.empty(0)
eta_field = np.empty(0)
eta_inv = np.empty(0)
Tco_mpp = np.empty(0)

for i in range (sys_no):
    tilt = np.append(tilt, np.deg2rad(sys_par.tilt[i]))
    panaz = np.append(panaz, np.deg2rad(sys_par.panaz[i]))
    Umpp0 = np.append(Umpp0, sys_par.Umpp0[i])
    Impp0 = np.append(Impp0, sys_par.Impp0[i])
    moh = np.append(moh, sys_par.moh[i])
    mow = np.append(mow, sys_par.mow[i])
    npar = np.append(npar, sys_par.npar[i])
    nser = np.append(nser, sys_par.nser[i])
    Hco = np.append(Hco, sys_par.Hco[i])
    eta_dirt = np.append(eta_dirt, sys_par.eta_dirt[i])
    eta_field = np.append(eta_field, sys_par.eta_field[i])
    eta_inv = np.append(eta_inv, sys_par.eta_inv[i])
    Tco_mpp = np.append(Tco_mpp, sys_par.tco_mpp[i])
    
i = np.array(range(1,366))       
dec = 23.45 * np.sin((np.deg2rad(360*(284+i)/365))) 
for i in range(1,366):  #i = doy          
    dec = 23.45 * m.sin((m.radians(360*(284+i)/365))) #deg
    b = (i - 1) * (360. /365) #deg
    eot = (180*4/m.pi) * (0.000075 + 0.001868*m.cos(m.radians(b)) - 0.032077*m.sin(m.radians(b)) - 0.014615*m.cos(2*m.radians(b)) - 0.0409*m.sin(2*m.radians(b)))  # in min    
    for j in range(0,24):
        if i in range(86,304): 
            if j > 1:  #day light saving between 27. Mar, 02:00 and 30. Oct, 03:00 in 2005
                d = 1   
            else:
                d = 0
        ts = j + eot/60 - (longst - longloc)/15 - d     #hr
        hra = 15 * (ts - 12)   #deg
        Dec = np.append(Dec, dec)
        EoT = np.append(EoT, eot) 
        I = np.append(I, i)
        J = np.append(J, j)
        TS = np.append(TS, ts)
        HrA = np.append(HrA, hra)
    #Solar angles        
        ele = m.asin(m.sin(m.radians(latloc)) * m.sin(m.radians(dec)) + (m.cos(m.radians(latloc)) * m.cos(m.radians(dec)) * m.cos(m.radians(hra)))) #rad
        ze = m.pi/2 - ele           #rad
        Ele = np.append(Ele, m.degrees(ele)) #deg
        Ze = np.append(Ze, m.degrees(ze)) #deg
        if m.cos(m.radians(hra)) < (m.tan(m.radians(dec)) / m.tan(m.radians(latloc))):
            az = 2*m.pi + m.asin(-1 * m.cos(m.radians(dec)) * m.sin(m.radians(hra))/ m.cos(ele)) #rad
        else:
            az = m.pi - m.asin(-1 * m.cos(m.radians(dec)) * m.sin(m.radians(hra))/ m.cos(ele)) 
        if az > (2 * m.pi):
            az = az - 2 * m.pi
        for i in range(sys_no):
            Theta = np.append(Theta, pd.Series([m.degrees(m.acos(m.sin(ele)*m.cos(tilt[i]) + m.cos(ele)*m.sin(tilt[i])*m.cos(panaz[i] + az)))]))
               
        Az = np.append(Az, m.degrees(az)) #deg
        
Theta.resize((8760,sys_no))
bni = bhi / np.abs(np.sin(np.deg2rad(Ele)))  #Quaschning
for i in range(8760):
    if bni[i]/bhi[i] > 1.5:
        bni[i] = 1.5*bhi[i]

## Step 2: Calculation of global irradiance on a tilted surface
          
albedo = 0.15              # minimum for urban medium     
theta = np.array(Theta)       
ze = np.array(Ze)
az = np.array(Az)
ele = np.array(Ele)
bti = np.empty(0)

bti = np.append(bti, bhi * np.abs((np.cos(np.deg2rad(theta[:,0]))/np.sin(np.deg2rad(ele)))))
for i in range(1, sys_no):
    bti = np.vstack((bti, bhi * np.abs((np.cos(np.deg2rad(theta[:,i]))/np.sin(np.deg2rad(ele))))))
bti = bti.T

if sys_no >= 2:
    for i in range(8760):
        for j in range(sys_no): 
            if bti[i,j]/bhi[i] > 1.5:
                bti[i,j] = 1.5*bhi[i]
else:
    for i in range(8760):
        if bti[i]/bhi[i] > 1.5:
            bti[i] = 1.5*bhi[i]
       
#perez
bni_extra = pv.irradiance.extraradiation(I,1367)
airmass = pv.atmosphere.relativeairmass(Ze)
airmass = np.nan_to_num(airmass)
dti_per = np.empty(0)

dti_per = pv.irradiance.perez(tilt[0],
                          panaz[0],
                          pd.Series(dhi, index = range(len(dhi))),
                          pd.Series(bni, index = range(len(bni))),
                          pd.Series(bni_extra, index = range(len(bni_extra))),
                          pd.Series(Ze, index = range(len(Ze))),
                          pd.Series(Az, index = range(len(Az))),
                          pd.Series(airmass, index = range(len(airmass)))).reindex(range(8760)).fillna(0)
for i in range(1, sys_no):
    dti_per = np.vstack((dti_per, 
                         pv.irradiance.perez(tilt[i],
                              panaz[i],
                              pd.Series(dhi, index = range(len(dhi))),
                              pd.Series(bni, index = range(len(bni))),
                              pd.Series(bni_extra, index = range(len(bni_extra))),
                              pd.Series(Ze, index = range(len(Ze))),
                              pd.Series(Az, index = range(len(Az))),
                              pd.Series(airmass, index = range(len(airmass)))).reindex(range(8760)).fillna(0)))
dti_per = dti_per.T

dri = np.empty(0)
dri = np.empty(0)

dri = ghi * albedo * (1 - np.cos(tilt[0])) / 2
for i in range(1, sys_no):
    dri = np.vstack((dri, ghi * albedo * (1 - np.cos(tilt[i])) / 2))
dri = dri.T


gti = bti + dti_per + dri 


## Step 3: Calculation of net output power including various loss schemes

gti0 = 1000.          #ref. GTI in W/m2
Tref = 25.            #ref. PV temp. in deg
Tamb = temp - 273.15   #ambient temp.
Tamb[Tamb < 0] = 0

dmod = 0.      #distance between module edges in parallel strings


area_mo = moh * mow   #module area in m2

Psys = np.empty(0)


if sys_no >= 2:
    i = 0
    Umpp = Umpp0[i] * np.log(gti[:,i]) / np.log(gti0)
    Impp = Impp0[i] * gti[:,i]/gti0
    Tpan = Tamb + gti[:,i]*Hco[i]              #panel temperature
    Pmpp = nser[i] * npar[i] * Umpp * Impp * (1 + Tco_mpp[i]*(Tpan - Tamb)) 
    Psys = Pmpp * eta_dirt[i] * eta_field[i] * eta_inv[i]        #Watt
    
    for i in range(1,sys_no):
        Umpp = Umpp0[i] * np.log(gti[:,i]) / np.log(gti0)
        Impp = Impp0[i] * gti[:,i]/gti0
        Tpan = Tamb + gti[:,i]*Hco[i]
        Pmpp = nser[i] * npar[i] * Umpp * Impp * (1 + Tco_mpp[i]*(Tpan - Tamb)) 
        Psys = np.vstack((Psys, Pmpp * eta_dirt[i] * eta_field[i] * eta_inv[i]))    #Watt
    Psys = Psys.T    
    Psys = np.nan_to_num(Psys)
    
    k = idx
    
    energy_sim = np.zeros((8760,sys_no))
    
    for i in range(k,(k+23)):   
        for j in range(sys_no):
            energy_sim[i,j] = energy_sim[i-1,j] + Psys[i,j]   #Wh
    
    Energy_sim = energy_sim[k:(k+23)]
    epoch = rawdata.index.astype(np.int64) //10**9
    epoch = np.column_stack((epoch, Energy_sim))
    system_id = np.empty(0)
    system_id = 0
    for i in range(0,sys_no):
        system_id = np.append(system_id, sys_par.sys_id[i])
    system_id = system_id.T
    epoch = np.vstack([system_id, epoch])
    out_fil = fileName.split('.'); 
    out_file = out_fil[0]+"_SimulatedEnergy"+".csv"
    np.savetxt(out_file,epoch,fmt="%.2f",delimiter=",")
    
else:
    Umpp = Umpp0 * np.log(gti) / np.log(gti0)
    Impp = Impp0 * gti/gti0
    Tpan = Tamb + gti*Hco               #panel temperature
    Pmpp = nser * npar * Umpp * Impp * (1 + Tco_mpp*(Tpan - Tamb)) 
    Psys = Pmpp * eta_dirt * eta_field * eta_inv        #Watt
    Psys = np.nan_to_num(Psys)
    
    Energy = np.sum(Psys)   #Wh
    
    k = idx
    energy_sim = np.zeros(8760)
    
    for i in range(k,(k+23)):   
        energy_sim[i] = energy_sim[i-1] + Psys[i]   #Wh
    
    Energy_sim = energy_sim[k:(k+23)]
    
    epoch = rawdata.index.astype(np.int64) //10**9
    out_fil = fileName.split('.'); 
    out_file = out_fil[0]+"_SimulatedEnergy"+".csv"
    system_id = sys_par.sys_id[0]
    with open(out_file, 'wb') as csvfile:
        wr = csv.writer(csvfile, delimiter=',')
        wr.writerow(['', system_id ])
        for i in range(23):
            wr.writerow([epoch[i] , Energy_sim[i]])
    

