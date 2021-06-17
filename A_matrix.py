# -*- coding: utf-8 -*-
"""
Created on Fri May 21 11:21:32 2021

@author: jbarker
"""

#import scipy as sp
import numpy as np
#import sys
#import string
#import math as m
#import config as cg
import functions as fc
import MainCode as MC

#from operator import itemgetter
#from collections import namedtuple

   
Nominal_coords = MC.Nominal_coords   
LoS_measurements = MC.LoS_measurements
Pol_measurements = MC.Pol_measurements
Transformed_Pol_measurements = MC.Transformed_Pol_measurements
StDevs_IFM_measurements = MC.StDevs_IFM_measurements
measured_distances_in_lines = MC.measured_distances_in_lines
sorted_measured_points_in_lines = MC.sorted_measured_points_in_lines
Two_epochs = MC.Two_epochs

#if Two_epochs:
#    LoS_measurements_E1 = MC.LoS_measurements_E1
#    Pol_measurements_E1 = MC.Pol_measurements_E1
#    Transformed_Pol_measurements_E1 = MC.Transformed_Pol_measurements_E1
#    StDevs_IFM_measurements_E1 = MC.StDevs_IFM_measurements_E1
#    measured_distances_in_lines_E1 = MC.measured_distances_in_lines_E1
#    sorted_measured_points_in_lines_E1 = MC.sorted_measured_points_in_lines_E1

count_IFM_measurements = sum([len(v) for k, v in\
                                         measured_distances_in_lines.items()])
count_Pico_measurements = 0
count_Pol_measurements = (sum([len(v) for k, v in Pol_measurements.items()]))
                        
count_all_observations = count_IFM_measurements + count_Pico_measurements \
                         + 3*count_Pol_measurements
del count_IFM_measurements, count_Pico_measurements

unknowns,count_unknowns,count_instruments = fc.find_unknowns(
                                                  Transformed_Pol_measurements)

#if Two_epochs:
#    unknowns_E1 = fc.find_unknowns(Pol_measurements_E1)
#   if cg.Print_epoch_checks:
#        if unknowns==unknowns_E1:
#            print('Unknowns in both epoch match')
#        else:
#            print("Unknowns in epochs don't match")

A_matrix = np.zeros([count_all_observations,count_unknowns])
A_matrixHR = {}

L_vector = np.array([])
L_vectorHR = []

Aproximates = fc.merge_measured_coordinates(Transformed_Pol_measurements)

X_vector, X_vectorHR = fc.filling_X(
                      Aproximates, unknowns, count_unknowns, count_instruments)

# Filling A and L with IFM measurements
for line in measured_distances_in_lines:
    # meas_i is index of the measurand in line, so I can pair it with the
    # Point IDs from sorted points in lines, first measured point is on the
    # same index as the distance and second point is on index + 1
    for meas_i,distance in enumerate(measured_distances_in_lines[line]):
        # I need index of the measurement in L vector, so I can put it on
        # correct corresponding row in First plan matrix A
        L_i = len(L_vector)
        L_vector = np.append(L_vector, distance)
        """Now figuring the index of points in the unknowns list, so I know
           which column of the A matrix. The original index is multiplied by 3
           because unknowns are names of points (and instrument orientations)
           not a complete list of unknowns = Point X,Y and Z => *3         """
        PointFrom = sorted_measured_points_in_lines[line][meas_i]
        PointTo = sorted_measured_points_in_lines[line][meas_i+1]
        PointFrom_i = 3*unknowns.index(PointFrom) 
        PointTo_i = 3*unknowns.index(PointTo)
        dX,dY,dZ = fc.ParD_sd(Aproximates[PointTo],Aproximates[PointFrom])
        A_matrix[L_i,PointTo_i:PointTo_i+3] = dX,dY,dZ
        # for point "From" the partial derivatives change sign
        A_matrix[L_i,PointFrom_i:PointFrom_i+3] = -dX,-dY,-dZ
        # Documenting in human readible format what are the A and L elements
        L_vectorHR.append((line, PointFrom, PointTo))
        A_matrixHR[(L_i,PointFrom_i)] = ['dX', line, PointFrom, PointTo]
        A_matrixHR[(L_i,PointFrom_i+1)] = ['dY', line, PointFrom, PointTo]
        A_matrixHR[(L_i,PointFrom_i+2)] = ['dZ', line, PointFrom, PointTo]
        A_matrixHR[(L_i,PointTo_i)] = ['dX', line, PointTo, PointFrom]
        A_matrixHR[(L_i,PointTo_i+1)] = ['dY', line, PointTo, PointFrom]
        A_matrixHR[(L_i,PointTo_i+2)] = ['dZ', line, PointTo, PointFrom]
del PointFrom,PointTo, PointFrom_i,PointTo_i,dX,dY,dZ,L_i, meas_i, distance

L_subv_Hz = np.array([])
L_subv_V = np.array([])
L_subv_sd = np.array([])
L_subv_Hz_HR = []
L_subv_V_HR = []
L_subv_sd_HR = []

counter = 0
for inst,points in Pol_measurements.items():
    instrument_i = 3 * unknowns.index(inst) # Starting column of the instrument
    Ori_instrument_i = X_vectorHR.index('Ori_'+inst) # Inst's Orientation index
    for point in points:
        # evaluating the partial derivatives for all polar observations
        Hz_dX, Hz_dY, Hz_dZ, Hz_dO = fc.ParD_Hz(Aproximates[point],
                                                Aproximates[inst])
        V_dX, V_dY, V_dZ = fc.ParD_V(Aproximates[point],Aproximates[inst])
        sd_dX, sd_dY, sd_dZ = fc.ParD_sd(Aproximates[point],Aproximates[inst])
        # Returning measured values
        sd,Hz,V = Pol_measurements[inst][point][0:3]
        # Filling the L subvectors for Hz,V and sd
        L_subv_Hz = np.append(L_subv_Hz, Hz)
        L_subv_V = np.append(L_subv_V, V)
        L_subv_sd = np.append(L_subv_sd, sd)
        # Filling the Human readible version of L subvectors
        L_subv_Hz_HR.append(('Hz', inst, point))
        L_subv_V_HR.append(('V', inst, point))
        L_subv_sd_HR.append(('sd', inst, point))
        # Returning the starting column of the point
        Point_i = 3*unknowns.index(point)
        # Row offsets of V and sd measurements (allows filling in same loop)
        Hz_offset = count_all_observations - 3*count_Pol_measurements
        V_offset = count_all_observations - 2*count_Pol_measurements
        sd_offset = count_all_observations - count_Pol_measurements
        # Filling A with Hz partial derivatives
        A_matrix[Hz_offset+counter,Point_i:Point_i+3] = Hz_dX, Hz_dY, Hz_dZ
        A_matrix[V_offset+counter,Point_i:Point_i+3] = V_dX, V_dY, V_dZ
        A_matrix[sd_offset+counter,Point_i:Point_i+3] = sd_dX, sd_dY, sd_dZ
        A_matrix[Hz_offset+counter,Ori_instrument_i] = Hz_dO
        A_matrix[Hz_offset+counter,instrument_i:instrument_i+3] = \
                                                         -Hz_dX, -Hz_dY, -Hz_dZ
        A_matrix[V_offset+counter,instrument_i:instrument_i+3] = \
                                                            -V_dX, -V_dY, -V_dZ
        A_matrix[sd_offset+counter,instrument_i:instrument_i+3] = \
                                                         -sd_dX, -sd_dY, -sd_dZ
        # Filling Human readible A matrix
        A_matrixHR[(Hz_offset+counter,Point_i)] = ['Hz/dX', inst, point]
        A_matrixHR[(Hz_offset+counter,Point_i+1)] = ['Hz/dY', inst, point]
        A_matrixHR[(Hz_offset+counter,Point_i+2)] = ['Hz/dZ', inst, point]
        A_matrixHR[(V_offset+counter,Point_i)] = ['V/dX', inst, point]
        A_matrixHR[(V_offset+counter,Point_i+1)] = ['V/dY', inst, point]
        A_matrixHR[(V_offset+counter,Point_i+2)] = ['V/dZ', inst, point]
        A_matrixHR[(sd_offset+counter,Point_i)] = ['sd/dX', inst, point]
        A_matrixHR[(sd_offset+counter,Point_i+1)] = ['sd/dY', inst, point]
        A_matrixHR[(sd_offset+counter,Point_i+2)] = ['sd/dZ', inst, point]
        counter += 1
L_vector = np.append(L_vector,[L_subv_Hz,L_subv_V,L_subv_sd])
L_vectorHR = L_vectorHR + L_subv_Hz_HR + L_subv_V_HR + L_subv_sd_HR
print('End of A_matrix code')