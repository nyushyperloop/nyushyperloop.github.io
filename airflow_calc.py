from math import pi
import numpy as np

import pylab as p

import openmdao #from openmdao.main.api import Component
from openmdao.lib.datatypes.api import Float

from pycycle.flowstation import AirFlowStation, secant

class TubeLimitFlow(openmdao.Component): 
    """Finds the limit velocity for a body traveling through a tube"""
    #Inputs
    radius_tube = Float(111.5 , iotype="in", units="cm", desc="required radius for the tube")    
    radius_inlet = Float(73.7, iotype="in", units="cm", desc="radius of the inlet at it's largest point")
    Ps_tube = Float(99, iotype="in", desc="static pressure in the tube", units="Pa") 
    Ts_tube = Float(292.1, iotype="in", desc="static temperature in the tube", units="degK")
    Mach_pod = Float(1.0, iotype="in", desc="travel Mach of the pod")
    Mach_bypass = Float(.95, iotype="in", desc="Mach in the air passing around the pod")
    #Outputs
    limit_speed = Float(iotype="out", desc="pod travel speed where flow choking occurs", units="m/s")
    limit_Mach = Float(iotype="out", desc="pod travel Mach number where flow choking occurs")
    W_excess = Float(iotype="out", desc="excess tube mass flow above the Kantrowitz limit", units="kg/s")
    W_tube = Float(iotype="out", desc="Tube demand flow", units="kg/s")
    W_kant = Float(iotype="out", desc="Kantrowitz limit flow", units="kg/s")
    #mu_air = Float(iotype="out", desc="dynamic viscosity of air", units="Pa*s")

    def execute(self):

        fs_tube = self.fs_tube = AirFlowStation()
        tube_rad = self.radius_tube*0.0328084 #convert to ft
        inlet_rad = self.radius_inlet*0.0328084

        self._tube_area  = pi*(tube_rad**2) #ft**2
        self._bypass_area = pi*(tube_rad**2-inlet_rad**2)

        self._Ts = self.Ts_tube*1.8 #convert to R
        self._Ps = self.Ps_tube*0.000145037738 #convert to psi


        area_ratio_target = self._tube_area/self._bypass_area

        def f(m_guess): 
            fs_tube.setStaticTsPsMN(self._Ts, self._Ps , m_guess)
            gam = fs_tube.gamt
            g_exp = (gam+1)/(2*(gam-1))
            ar = ((gam+1)/2)**(-1*g_exp)*((1+ (gam-1)/2*m_guess**2)**g_exp)/m_guess
            return ar - area_ratio_target

        self.limit_Mach = secant(f, .3, x_min=0, x_max=1)
        self.limit_speed = fs_tube.Vflow*0.3048 #convert to meters
        
        #excess mass flow calculation
        fs_tube.setStaticTsPsMN(self._Ts, self._Ps, self.Mach_pod)
        self.W_tube = fs_tube.rhos*fs_tube.Vflow*self._tube_area*0.45359

        fs_tube.Mach = self.Mach_bypass #Kantrowitz flow is at these total conditions, but with Mach 1
        self.W_kant = fs_tube.rhos*fs_tube.Vflow*self._bypass_area*0.45359
        #print "test", fs_tube.rhos, fs_tube.Vflow, self._bypass_area, self.W_kant

        self.W_excess = self.W_tube - self.W_kant

        #self.mu_air = self.fs_tube.mu/0.671968975


def plot_data(comp, c='b'):
    """utility function to make the Kantrowitz Limit Plot""" 


    MN = []
    W_tube = []
    W_kant = []

    for m in np.arange(.1,1.1,.1): 
        comp.Mach_pod = m
        comp.run()
        #print comp.radius_tube, comp.Mach_pod, comp.W_tube, comp.W_kant, comp.W_excess

        MN.append(m)
        W_kant.append(comp.W_kant)
        W_tube.append(comp.W_tube)

    fig = p.plot(MN,W_tube, '-', label="R=%d Req. Flow"%comp.radius_tube, lw=3, c=c)
    p.plot(MN,W_kant, '--', label="R=%d Limit Flow"%comp.radius_tube,   lw=3, c=c)
    #p.legend(loc="best")
    p.xlabel('Pod Mach Number')
    p.ylabel('Flow Rate (kg/sec)')
    p.title('Tube Limit Flow')

    return fig


    #print np.array(W_tube)- np.array(W_kant)

        


if __name__ == "__main__": 

    from openmdao.main.api import set_as_top
    comp = set_as_top(TubeLimitFlow())
    comp.radius_tube = 100
    comp.run()
    #print comp.Mach_pod, comp.W_tube, comp.W_kant, comp.W_excess
    #print comp.MN[-1]
    #print comp.W_tube[-1]
    #print comp.W_kant[-1]
    plot_data(comp,c='b')

    comp.radius_tube = 150
    plot_data(comp,c='g')

    comp.radius_tube = 200
    plot_data(comp,c='r')

    p.legend(loc="best")
    p.show()
