#!/usr/bin/python2
# -*- coding: utf-8 -*-

import numpy as np
import os

import sys
sys.path.append(os.path.pardir)

import settings as st
#-------------------------------------------------------------
# settings
#-------------------------------------------------------------
end_time = 20
yd = 3 #[m]

controllerList = ['FController', 'GController', 'JController',\
                'LSSController', 'PIFeedbackController', 'all']

#-------------------------------------------------------------
# init
#-------------------------------------------------------------
print '\n ### Regimefile Generator Eval C2 ### \n'

#print 'Choose parameter to test: '
#for idx, param in enumerate(st.paramVariationDictC1.keys()):
    #print '\t',idx,' - ', param

#paramIdx = -1
#while paramIdx not in range(0, len(st.paramVariationDictC1.keys())):
    #paramIdx = input()

paramIdx = 0

# extract parameter values
parameter = st.paramVariationDictC2.keys()[paramIdx]
lower_bound = st.paramVariationDictC2[parameter]['lower_bound']
upper_bound = st.paramVariationDictC2[parameter]['upper_bound']
step_size = st.paramVariationDictC2[parameter]['step_size']
simLimits = np.arange(lower_bound, upper_bound + step_size, step_size)

print 'Choose controller: '
for idx, controller in enumerate(controllerList):
    print '\t',idx,' - ', controller

controlIdx = -1
while controlIdx not in range(0, len(controllerList)):
    controlIdx = input()

if controlIdx == len(controllerList)-1:
    simCases = controllerList[:-1]
else:
    simCases = [controllerList[controlIdx]]

#-------------------------------------------------------------
# functions
#-------------------------------------------------------------

#prefined strings
def writeRegime(cName, pole, param, paramVal, appendix):
    return '- name: C2_' + cName + '_poles(' + str(pole) + ')'\
                    + '_' + parameter +'(' + str(paramVal) + ')'\
                    + appendix + '\n'\
                    + '  clear previous: !!python/bool False \n\n'

def writeModel(param, paramVal):
    return '  model:' + '\n'\
            + '   type: BallBeamModel' + '\n'\
            + '   ' + parameter + ': ' + str(paramVal) + '\n\n'

def writeController(cName, pole, multiplicator):
    tmp = '  controller: ' + '\n'\
            + '   type: '  + controller + '\n'\
            + '   poles: ' + str([pole]*multiplicator) + '\n'

    if (controller == 'PIFeedbackController' or controller == 'LSSController'):
        tmp += '   r0: ' + str(yd) + '\n'
    tmp += '\n'
    return tmp

def writeSensor(senName, paramVal):
    return '  sensor:' + '\n'\
            + '   type: ' + senName + '\n'\
            + '   delay: ' + str(paramVal) + '\n'\
            + '   output: ' + '[0,1,2,3]' + '\n\n'

def writeDisturbance(disName, paramVal):
    if paramVal == 0:
        return '  disturbance:' + '\n'\
            + '   type: None\n'

    return '  disturbance:' + '\n'\
            + '   type: ' + disName + '\n'\
            + '   mean value: ' + '0' + '\n'\
            + '   sigma: ' + str(paramVal) + '\n\n'

def saveOutput(output, cName, poles, parameter, limits):
    '''
        wrapper to save regime file
    '''
    dirPath = os.path.join(os.path.pardir, os.path.pardir, 'regimes', 'generated')

    if not os.path.isdir(dirPath):
        os.makedirs(dirPath)

    fileName = 'C2_' + cName + '_poles' + str(poles) \
                        + '_' + str(parameter)\
                        + '(' + str(simLimits[0]) + ',' + str(simLimits[-1])\
                        + ').sreg'

    filePath = os.path.join(dirPath, fileName)
    with open(filePath, 'w') as f:
        f.write(output)

#-------------------------------------------------------------
# preamble
#-------------------------------------------------------------
preamble = '- name: C2-simulation-setup\n'\
+'  clear previous: !!python/bool True\n'\
+'\n'\
+'  model:\n'\
+'   type: BallBeamModel\n'\
+'\n'\
+'  solver:\n'\
+'   type: VODESolver\n'\
+'   end time: '+str(end_time)+'\n'\
+'\n'\
+'  trajectory:\n'\
+'   type: SmoothTransitionTrajectory\n'\
+'   Positions: [0, ' + str(yd) + ']\n'\
+'   start time: 0\n'\
+'   delta t: 5\n'\
+'\n'

#-------------------------------------------------------------
# main
#-------------------------------------------------------------
collection = ''
for controller in simCases:
    lines = preamble

    # how many poles?
    if controller == 'PIFeedbackController':
        multiplicator = 5
    else:
        multiplicator = 4

    #set correct poles
    poles = st.poles[controller]

    #search limits
    for val in simLimits:
        lines += writeRegime(controller, poles, parameter, val, '')
        lines += writeController(controller, poles, multiplicator)
        if parameter == 'sigma':
            lines += writeDisturbance('GaussianNoiseDisturbance', val)
        if parameter == 'delay':
            lines += writeSensor('DeadTimeSensor', val)   
        lines += '\n\n'

        saveOutput(lines, controller, poles, parameter, simLimits)

    collection += lines

if len(simCases) > 1:
    saveOutput(collection, 'all', '_', parameter, simLimits)

print 'done.'
