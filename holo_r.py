#!/usr/bin/python
#coding=utf-8

import os
import cv2
import time
import sys
import numpy as np
import matplotlib.pyplot as plt

#########################
# g_tree = [[,],[,]]
# res = 2D array
def merger(g_tree):
    if type(g_tree[0][0]) == list:
        A11 = merger(g_tree[0][0])
        A12 = merger(g_tree[0][1])
        A21 = merger(g_tree[1][0])
        A22 = merger(g_tree[1][1])
        
        #res = np.array([[A11,A12],[A21,A22]])
        res = np.vstack((np.hstack((A11,A12)),np.hstack((A21,A22))))
    else:
        #res = np.array(g_tree)
        res = np.vstack((np.hstack((g_tree[0][0],g_tree[0][1])),np.hstack((g_tree[1][0],g_tree[1][1]))))
    return res

# rotate(): rotate image  
# return: rotated image object  
def rotate(  
    img,  #image matrix  
    angle #angle of rotation  
    ):  
      
    height = img.shape[0]  
    width = img.shape[1]  
      
    if angle%180 == 0:  
        scale = 1  
    elif angle%90 == 0:  
        scale = float(max(height, width))/min(height, width)  
    else:  
        scale = np.sqrt(pow(height,2)+pow(width,2))/min(height, width)  
      
    #print 'scale %f\n' %scale  
          
    rotateMat = cv2.getRotationMatrix2D((width/2, height/2), angle, scale)  
    rotateImg = cv2.warpAffine(img, rotateMat, (width, height))  
    #cv2.imshow('rotateImg',rotateImg)  
    #cv2.waitKey(0)  
    #print("Angle[{}].size=[{},{}]".format(angle,rotateImg.shape[0],rotateImg.shape[1]))
      
    return rotateImg #rotated image  

#########################
def g_create():
    ksize = 9 # gabor尺度，6个
    lamda = np.pi/2 #波长
    kern = cv2.getGaborKernel((ksize, ksize), 1.0, 0, lamda, 0.5, 0, ktype=cv2.CV_32F)
    kern /= np.fabs(kern).sum()
    print(kern.sum())
    #kern -= kern.sum()
    
    return kern
    
#########################
def gfilter(gray, g):
    #accum = np.zeros_like(gray)
    #for kern in filters:
    #    fimg = cv2.filter2D(gray, cv2.CV_8UC3, gs)
    #    np.maximum(accum, fimg, accum)
#    A11 = cv2.filter2D(gray, cv2.CV_8UC3, gs[0][0])
#    A12 = cv2.filter2D(gray, cv2.CV_8UC3, gs[0][1])
#    A21 = cv2.filter2D(gray, cv2.CV_8UC3, gs[1][0])
#    A22 = cv2.filter2D(gray, cv2.CV_8UC3, gs[1][1])
#    
#    return [[A11,A12],[A21,A22]]
    #return cv2.filter2D(gray, cv2.CV_8UC3, g)
    
    accum = np.zeros_like(gray)
    fimg = cv2.filter2D(gray, -1, g)
    np.maximum(accum, fimg, accum)
    return accum
    
#########################
#gray = [],[[,],[,]]      
#gs = [[,],[,]]  
def g_trans(gray, gs):
    g_tree = []

    if type(gray) != list:
        gray_sub = gray
        A11 = gfilter(gray_sub, gs)
        A12 = gfilter(rotate(gray_sub,45), gs)
        A21 = gfilter(rotate(gray_sub,90), gs)
        A22 = gfilter(rotate(gray_sub,135), gs)
        #print("gray_shape=[{},{}]".format(A11.shape[0],A11.shape[1]))
        
        A11 = np.fabs(A11)
        A12 = np.fabs(A12)
        A21 = np.fabs(A21)
        A22 = np.fabs(A22)
        
        w = gray_sub.shape[1]
        h = gray_sub.shape[0]
        
        #g_tree = [[A11[2:(h-2),2:(w-2)],A12[2:(h-2),2:(w-2)]],[A21[2:(h-2),2:(w-2)],A22[2:(h-2),2:(w-2)]]]
        g_tree = [[A11,A12],[A21,A22]]
    else:
        A11 = g_trans(gray[0][0],gs)
        A12 = g_trans(gray[0][1],gs)
        A21 = g_trans(gray[1][0],gs)
        A22 = g_trans(gray[1][1],gs)
        
        g_tree = [[A11,A12],[A21,A22]]
    return g_tree

#########################
def create_pool_kern():
    filters = []
    ksize = [3] # gabor尺度，6个
    lamda = np.pi/2.0 #波长

    for theta in np.arange(0, np.pi, np.pi / 4): #gabor方向，0°，45°，90°，135°，共四个
        for K in range(len(ksize)): 
            kern = cv2.getGaborKernel((max(ksize), max(ksize)), 1.0, theta, lamda, 0.5, 0, ktype=cv2.CV_32F)
            kern /= kern.sum()
            kern -= kern.sum()
            filters.append(kern)      
            
    return filters   
        
#########################
# g_tree = [[,],[,]]
g_pool_kern = create_pool_kern()

def pool_max(g_tree):
    res = []
    
    if type(g_tree[0][0]) == list:
        A11 = pool_max(g_tree[0][0])
        A12 = pool_max(g_tree[0][1])
        A21 = pool_max(g_tree[1][0])
        A22 = pool_max(g_tree[1][1])
        res = [[A11,A12],[A21,A22]]
    else:
        w = g_tree[0][0].shape[1]
        h = g_tree[0][0].shape[0]

        #if w<=5 or h<=5:
        A11 = np.zeros((int((h-3)/2+1),int((w-3)/2+1)),dtype=np.uint8)
        A12 = np.zeros((int((h-3)/2+1),int((w-3)/2+1)),dtype=np.uint8)
        A21 = np.zeros((int((h-3)/2+1),int((w-3)/2+1)),dtype=np.uint8)
        A22 = np.zeros((int((h-3)/2+1),int((w-3)/2+1)),dtype=np.uint8)
        
        B11 = gfilter(g_tree[0][0], g_pool_kern[0])
        B12 = gfilter(g_tree[0][1], g_pool_kern[1])
        B21 = gfilter(g_tree[1][0], g_pool_kern[2])
        B22 = gfilter(g_tree[1][1], g_pool_kern[3])
        
            
        for i in range(1,h-1,2):
            for k in range(1,w-1,2):
                A11[int((i-1)/2)][int((k-1)/2)] = B11[i][k] #np.amax(g_tree[0][0][(i-1):(i+1),(k-1):(k+1)])
                #A11[int((i-1)/2)][int((k-1)/2)] = np.amax(g_tree[0][0][(i-1):(i+1),(k-1):(k+1)])
                #A11[int((i-1)/2)][int((k-1)/2)] = g_tree[0][0][(i-1):(i+1),(k-1):(k+1)].sum()/9
                    
        for i in range(1,h-1,2):
            for k in range(1,w-1,2):
                A12[int((i-1)/2)][int((k-1)/2)] = B12[i][k] #np.amax(g_tree[0][1][(i-1):(i+1),(k-1):(k+1)])
                #A12[int((i-1)/2)][int((k-1)/2)] = np.amax(g_tree[0][1][(i-1):(i+1),(k-1):(k+1)])
                #A12[int((i-1)/2)][int((k-1)/2)] = g_tree[0][1][(i-1):(i+1),(k-1):(k+1)].sum()/9
        
        for i in range(1,h-1,2):
            for k in range(1,w-1,2):
                A21[int((i-1)/2)][int((k-1)/2)] = B21[i][k] #np.amax(g_tree[1][0][(i-1):(i+1),(k-1):(k+1)])
                #A21[int((i-1)/2)][int((k-1)/2)] = np.amax(g_tree[1][0][(i-1):(i+1),(k-1):(k+1)])
                #A21[int((i-1)/2)][int((k-1)/2)] = g_tree[1][0][(i-1):(i+1),(k-1):(k+1)].sum()/9
                    
        for i in range(1,h-1,2):
            for k in range(1,w-1,2):
                A22[int((i-1)/2)][int((k-1)/2)] = B22[i][k] #np.amax(g_tree[1][1][(i-1):(i+1),(k-1):(k+1)])
                #A22[int((i-1)/2)][int((k-1)/2)] = np.amax(g_tree[1][1][(i-1):(i+1),(k-1):(k+1)])
                #A22[int((i-1)/2)][int((k-1)/2)] = g_tree[1][1][(i-1):(i+1),(k-1):(k+1)].sum()/9
        
        #print("pool_size=[{},{}]".format(A11.shape[0],A11.shape[1]))
        
        res = [[A11,A12],[A21,A22]]    
                
    return res
        
if len(sys.argv) != 2:
    print("input img")
    exit()  
    
img_path = sys.argv[1] #"."      
img = cv2.imread(img_path,0) #read as gray
#gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = np.float32(img)
imgW = img.shape[1]
imgH = img.shape[0]

stride = 2
np.set_printoptions(threshold = 1e6)

gs = g_create()

# 1
conv = g_trans(gray,gs)

plt.figure(1)
plt.subplot(2,2,1)
plt.imshow(conv[0][0],cmap="gray")
plt.subplot(2,2,2)
plt.imshow(conv[0][1],cmap="gray")
plt.subplot(2,2,3)
plt.imshow(conv[1][0],cmap="gray")
plt.subplot(2,2,4)
plt.imshow(conv[1][1],cmap="gray")

## 2
#pool = pool_max(conv)
#del conv
#
#plt.figure(1)
#plt.subplot(2,2,1)
#plt.imshow(pool[0][0])
#plt.subplot(2,2,2)
#plt.imshow(pool[0][1])
#plt.subplot(2,2,3)
#plt.imshow(pool[1][0])
#plt.subplot(2,2,4)
#plt.imshow(pool[1][1])

##conv = g_trans(pool,gs)
#del pool
#print("2")
#
#
## 3
#pool = pool_max(conv)
#del conv
#conv = g_trans(pool,gs)
#del pool
#print("3")

##4
#pool = pool_max(conv)
#del conv
#conv = g_trans(pool,gs)
#del pool
#print("4")

#
##5
#pool = pool_max(conv)
#del conv
#conv = g_trans(pool,gs)
#del pool
#print("5")
#
##6
#pool = pool_max(conv)
#del conv
#conv = g_trans(pool,gs)
#del pool
#print("6")


#disp = merger(conv)
#print(disp)
#plt.imshow(disp)

#plt.show()
