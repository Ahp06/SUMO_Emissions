'''
Created on 6 nov. 2018

@author: Admin
'''

class Area:
    
    locked = False 
    
    def __init__(self, coords):
        self.coords = coords
    
    
    def getCoords(self):
        return self.coords
    