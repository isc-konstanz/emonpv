# -*- coding: utf-8 -*-
"""
Created on Thu May 07 14:45:57 2015

@author: ama
"""

import numpy as np
import pandas as pd
import matplotlib.path as mplPath
import math as m
import pvlib as pv
import fnmatch
import os
import csv
       
h = pd.date_range('20150101', periods= 8760, freq= 'H', tz="Europe/Berlin")

for file in os.listdir('.'):
    if fnmatch.fnmatch(file, '??_??????????.csv'): 
        #print file
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

for i in range(8760):
    for j in range(sys_no): 
        if bti[i,j]/bhi[i] > 1.5:
            bti[i,j] = 1.5*bhi[i]
       
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

#Hco = 0.045           #heat up coefficient in deg.C/(W/m2) | same as old
#eta_dirt = 1.       #dirt factor | same as old
#eta_field = 1.      #field efficiency | same as old
#eta_inv = 0.96        #inverter efficiency | same as old
#Tco_mpp = -0.0042     #temp. coeff. 
dmod = 0.      #distance between module edges in parallel strings


area_mo = moh * mow   #module area in m2

Psys = np.empty(0)

i = 0
Umpp = Umpp0[i] * np.log(gti[:,i]) / np.log(gti0)
Impp = Impp0[i] * gti[:,i]/gti0
Tpan = Tamb + gti[:,i]*Hco[i]              #panel temperature
Pmpp = nser[i] * npar[i] * Umpp * Impp * (1 + Tco_mpp[i]*(Tpan - Tamb)) 
Psys = Pmpp * eta_dirt[i] * eta_field[i] * eta_inv[i]        #Watt

for i in range(1,sys_no):
    Umpp = Umpp0[i] * np.log(gti[:,i]) / np.log(gti0)
    Impp = Impp0[i] * gti[:,i]/gti0
    Tpan = Tamb + gti[:,i]*Hco[i]               #panel temperature
    Pmpp = nser[i] * npar[i] * Umpp * Impp * (1 + Tco_mpp[i]*(Tpan - Tamb)) 
    Psys = np.vstack((Psys, Pmpp * eta_dirt[i] * eta_field[i] * eta_inv[i]))        #Watt
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
       
           

'''
for file in os.listdir('.'):
    if fnmatch.fnmatch(file, 'KN_????????00.csv'):   
        #for :00
        energy_sim[k-1] = np.array([0., 0., 0., 0., 0., 0., 0., 0., 0.])
        for i in range(k,(k+22)):         
            for j in range(9):
                energy_sim[i,j] = energy_sim[i-1,j] + Psys[i,j]/1000   #kWh
    elif fnmatch.fnmatch(file, 'KN_????????06.csv'):
        #for :06
        energy_sim[k-1] = np.array([1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3])
        for i in range(k,(k+22)):  
            for j in range(9):
                energy_sim[i,j] = energy_sim[i-1,j] + Psys[i,j]/1000   #kWh    
    elif fnmatch.fnmatch(file, 'KN_????????12.csv'):
        #for :12
        energy_sim[k-1] = np.array([38, 38, 38, 38, 38, 38, 38, 38, 38])
        for i in range(k,(k+22)):  
            for j in range(9):
                energy_sim[i,j] = energy_sim[i-1,j] + Psys[i,j]/1000   #kWh    
    elif fnmatch.fnmatch(file, 'KN_????????18.csv'):
        #for :18
        energy_sim[k-1] = np.array([72.2, 72.2, 72.2, 72.2, 72.2, 72.2, 72.2, 72.2, 72.2])
        for i in range(k,(k+22)):
            for j in range(9):
                energy_sim[i,j] = energy_sim[i-1,j] + Psys[i,j]/1000   #kWh

Energy = np.empty(0)
j = 0
Energy = np.sum(Psys[:,j])/1000.
for j in range(1,9):    
    Energy = np.vstack((Energy, np.sum(Psys[:,j])/1000.))   #kWh   
print 'Energy of first system = ' + str("%.2f" % Energy[0])+ ' kWh'   
print 'Energy of second system = ' + str("%.2f" % Energy[1])+ ' kWh' 
print 'Energy of third system = ' + str("%.2f" % Energy[2])+ ' kWh' 
print 'Energy of fourth system = ' + str("%.2f" % Energy[3])+ ' kWh' 
print 'Energy of fifth system = ' + str("%.2f" % Energy[4])+ ' kWh' 
print 'Energy of sixth system = ' + str("%.2f" % Energy[5])+ ' kWh' 
print 'Energy of seventh system = ' + str("%.2f" % Energy[6])+ ' kWh' 
print 'Energy of eighth system = ' + str("%.2f" % Energy[7])+ ' kWh' 
print 'Energy of ninth system = ' + str("%.2f" % Energy[8])+ ' kWh' 
print 'Total Energy of all systems = ' + str("%.2f" % (Energy[0]+Energy[1]+Energy[2]+Energy[3]
                                        +Energy[4]+Energy[5]+Energy[6]+Energy[7]
                                        +Energy[8]))+ ' kWh'       
'''         
 

'''
        
### Shading

# Clipping function
def clip(subjectPolygon, clipPolygon):   # Working
   def inside(p):
      return(cp2[0]-cp1[0])*(p[1]-cp1[1]) > (cp2[1]-cp1[1])*(p[0]-cp1[0])
   def computeIntersection():
      dc = [ cp1[0] - cp2[0], cp1[1] - cp2[1] ]
      dp = [ s[0] - e[0], s[1] - e[1] ]
      n1 = cp1[0] * cp2[1] - cp1[1] * cp2[0]
      n2 = s[0] * e[1] - s[1] * e[0] 
      n3 = 1.0 / (dc[0] * dp[1] - dc[1] * dp[0])
      return [(n1*dp[0] - n2*dc[0]) * n3, (n1*dp[1] - n2*dc[1]) * n3]
   outputList = subjectPolygon
   cp1 = clipPolygon[-1]
   for clipVertex in clipPolygon:
      cp2 = clipVertex
      inputList = outputList
      outputList = []
      s = inputList[-1]
      for subjectVertex in inputList:
         e = subjectVertex
         if inside(e):
            if not inside(s):
               outputList.append(computeIntersection())
            outputList.append(e)
         elif inside(s):
            outputList.append(computeIntersection())
         s = e
      cp1 = cp2
   outputList.append(outputList[0])   
   out = np.array(outputList)
   return(np.linalg.norm(np.cross((out[1]-out[0]),(out[3]-out[0]))))

def Shading():         
    az = np.array(np.deg2rad(Az))
    ele = np.array(np.deg2rad(Ele))
    tilta = np.full(8760,tilt)
    panaza = np.full(8760,panaz)
    s = np.array([(np.cos(az)*np.cos(ele)),(np.sin(az)*np.cos(ele)),np.sin(ele)]) #vector pointing at the sun in a {North,East,Zenith} rectangular coord. system 
    p111= np.full((8760,3),[0.,0.,0.])     # p111: Photovoltaic, first row, first column, first corner    
    p112= np.full((8760,3),[0.,moh*6,0.])
    p113= np.full((8760,3),[mow*np.cos(tilt),moh*6,mow*np.sin(tilt)])
    p114= np.full((8760,3),[mow*np.cos(tilt),0.,mow*np.sin(tilt)])         
    p211= np.full((8760,3),[dmod,0.,0.])
    p212= np.full((8760,3),[dmod,moh*6,0.])
    p213= np.full((8760,3),[(dmod+mow*np.cos(tilt)),moh*6,mow*np.sin(tilt)])
    p214= np.full((8760,3),[(dmod+mow*np.cos(tilt)),0.,mow*np.sin(tilt)])         
    a21_1 = np.cross((p211-p212),(p213-p212))  # vector normal to the shaded surface 2/ correct
    a21_2 = np.cross((p214-p211),(p212-p211))  # vector normal to the shaded surface 2/ correct

# Calculating reduced BTI  
    ps111 = np.empty(0)
    ps112 = np.empty(0)
    ps113 = np.empty(0)
    ps114 = np.empty(0)         
    fbti = np.empty(0)
    rbti = np.empty(0)
    s = np.transpose(s)
    areamo_1 = np.linalg.norm(np.cross((p112[0,:]-p111[0,:]),(p114[0,:]-p111[0,:]))) #mag. of cross product
    for i in range(8760):
        ps111 = np.append(ps111, (np.subtract(p111[i], np.dot((np.divide(np.dot(a21_2[i],(p111[i]-p211[i])),np.dot(a21_2[i],s[i]))),s[i]))))       
        ps112 = np.append(ps112, (np.subtract(p112[i], np.dot((np.divide(np.dot(a21_1[i],(p112[i]-p212[i])),np.dot(a21_1[i],s[i]))),s[i]))))    
        ps113 = np.append(ps113, (np.subtract(p113[i], np.dot((np.divide(np.dot(a21_1[i],(p113[i]-p212[i])),np.dot(a21_1[i],s[i]))),s[i]))))
        ps114 = np.append(ps114, (np.subtract(p114[i], np.dot((np.divide(np.dot(a21_2[i],(p114[i]-p211[i])),np.dot(a21_2[i],s[i]))),s[i]))))                         
    ps111 = np.reshape(ps111,(8760,3))
    ps112 = np.reshape(ps112,(8760,3))
    ps113 = np.reshape(ps113,(8760,3))
    ps114 = np.reshape(ps114,(8760,3))          
    area_sh = np.empty(0)
#    n2_val = [p211[0,0], p212[0,0], p213[0,0], p214[0,0]]      # Clip polygon (Module 2)
#    e2_val = [p211[0,1], p212[0,1], p213[0,1], p214[0,1]]
#    z2_val = [p211[0,2], p212[0,2], p213[0,2], p214[0,2]]
#    points = np.transpose(np.array([e2_val,n2_val,z2_val]))    # Module 2/ Clip points  
    loc0 = np.array([p211[0,1],p211[0,0],p211[0,2]])           # local origin/ changed to be in the form of [e,n,z]
    locx = np.array([p212[0,1],p212[0,0],p212[0,2]]) - loc0    # local X axis/ changed to be in the form of [e,n,z]
    normal = np.cross(locx, (np.array([p214[0,1],p214[0,0],p214[0,2]]) - loc0))  # vector orthogonal to polygon plane
    locy = np.cross(normal, locx)              # local Y axis
    len_locx = np.linalg.norm(locx)            # normalization of loc X axis
    len_locy = np.linalg.norm(locy)            # normalization of loc Y axis
    loc_xcoords = np.array([0,moh*6,moh*6,0])
    loc_ycoords = np.array([0,0,mow,mow]) 
    cpol = np.array([(loc_xcoords[0],loc_ycoords[0]),(loc_xcoords[1],loc_ycoords[1]),(loc_xcoords[2],loc_ycoords[2]),(loc_xcoords[3],loc_ycoords[3])]) 
    for i in range(8760):
        n1_val = [ps111[i,0], ps112[i,0], ps113[i,0], ps114[i,0]]  # Subject polygon (Shadows)
        e1_val = [ps111[i,1], ps112[i,1], ps113[i,1], ps114[i,1]]
        z1_val = [ps111[i,2], ps112[i,2], ps113[i,2], ps114[i,2]]  
# Defining local 2D coordinate system alligned to the second PV panel's plane (Lx,Ly)
        spoints = np.transpose(np.array([e1_val,n1_val,z1_val]))   # Shadow/ Subject points
        loc_xcoords_s = np.empty(0)
        loc_ycoords_s = np.empty(0)
        for i in np.arange(0,4):
            loc_xcoords_s = np.append(loc_xcoords_s, np.array(np.dot((spoints[i] - loc0), locx/len_locx)))   # local X coordinate/ Shadow
            loc_ycoords_s = np.append(loc_ycoords_s, np.array(np.dot((spoints[i] - loc0), locy/len_locy)))   # local Y coordinate/ Shadow
        spol = np.array([(loc_xcoords_s[0],loc_ycoords_s[0]),(loc_xcoords_s[1],loc_ycoords_s[1]),(loc_xcoords_s[2],loc_ycoords_s[2]), (loc_xcoords_s[3],loc_ycoords_s[3])])
        bbPath = mplPath.Path(cpol)
        if (bbPath.contains_point(np.array([loc_xcoords_s[0],loc_ycoords_s[0]])) == 0 
            and bbPath.contains_point(np.array([loc_xcoords_s[1],loc_ycoords_s[1]])) == 0
            and bbPath.contains_point(np.array([loc_xcoords_s[2],loc_ycoords_s[2]])) == 0 
            and bbPath.contains_point(np.array([loc_xcoords_s[3],loc_ycoords_s[3]])) == 0):
                area_ = 0.
                fbti_ = area_/areamo_1 
        else:
            area_ = clip(spol,cpol)
            fbti_ = area_/areamo_1   
        area_sh = np.append(area_sh, area_)
        fbti = np.append(fbti, fbti_)  
    rbti = (1-fbti) * bti   
#    print np.sum(bti/1000.)
#    print np.sum(rbti/1000.)          
        
# Calculating reduced DTI               
#    op111= np.full((8760,3),[m.pi,0.,0.])     
#    op112= np.full((8760,3),[(m.pi-np.arctan(moh*6/dmod)),0.,0.])    
    op113= np.full((8760,3),[(m.pi-np.arctan(moh*6/(dmod-mow*np.cos(tilt)))),np.arctan(mow*np.sin(tilt)/np.sqrt(np.square(moh*6)+np.square(dmod-mow*np.cos(tilt)))),0.])
    op114= np.full((8760,3),[m.pi,np.arctan(mow*np.sin(tilt)/(dmod-mow*np.cos(tilt))),0.])
    dhi_a = 0.5 * (op114[:,0]-op113[:,0])*np.square(np.sin(op114[:,1]))
    fdti = dhi_a / (m.pi/2 *(1+np.cos(tilt)))
    rdti = (1-fdti) * dti
#    print np.sum(dti/1000.)
#    print np.sum(rdti/1000.)          
    
# Calculating reduced PV output
    def rpvcalc(x,y,a,b):  #(tilt,panaz,rbti,rdti) in deg.
        dri = ghi * albedo * (1 - np.cos(np.deg2rad(x))) / 2     
        rgti = a + b + dri    
        rUmpp = Umpp0 * np.log(rgti) / np.log(gti0)
        rImpp = Impp0 * rgti/gti0
        rTpan = Tamb + rgti*Hco     #panel temperature
        rPmpp = nser * (((npar-1) * rUmpp * rImpp * (1 + Tco_mpp*(rTpan - Tamb)))+(1 * Umpp * Impp * (1 + Tco_mpp*(Tpan - Tamb)))) 
        rPsys = rPmpp * eta_dirt * eta_field * eta_inv    #Watt
        rPsys = np.nan_to_num(rPsys) 
        renergy = np.sum(rPsys)/1000.   #kWh
        return (renergy,rPsys)
    rEnergy, rPsys = rpvcalc(tilta,panaza,rbti,rdti)
    print 'Energy = ' + str("%.2f" % Energy)+ ' kWh' 
    print 'Reduced energy due to shading = ' + str("%.2f" % rEnergy)+ ' kWh'    
    print 'Energy loss due to shading = ' + str("%.2f" % (100*(1-(rEnergy/Energy)))) + ' %'
    return (rPsys,(rbti+rdti+dri))
#rPsys, rgti = Shading()

'''

'''

renergy_sim = np.zeros(8760)


#for 00
renergy_sim[k-1] = 49420.777
for i in range(k,5184):   
    renergy_sim[i] = renergy_sim[i-1] + rPsys[i]/1000   #kWh
  
#for 06
k = k+6
renergy_sim[k-1] = 49420.9
for i in range(k,5184):   
    renergy_sim[i] = renergy_sim[i-1] + rPsys[i]/1000   #kWh    
  
#for 12
k = k+12
renergy_sim[k-1] = 49445.1
for i in range(k,5184):   
    renergy_sim[i] = renergy_sim[i-1] + rPsys[i]/1000   #kWh    
    
#for 18
k = k+18
renergy_sim[k-1] = 49436.8
for i in range(k,5184):   
    renergy_sim[i] = renergy_sim[i-1] + rPsys[i]/1000   #kWh
'''


