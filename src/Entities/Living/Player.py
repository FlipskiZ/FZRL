import libtcodpy as TCOD

from src.Map.Map import Map, Tiles
from src import Constants

import random


class Player:
    instance = None
    
    def __init__(self, posX, posY, sightRadius=0):
        self.turnsAlive = 0

        self.posX = posX
        self.posY = posY

        self.sightRadius = sightRadius #0 is unlimited
        
        self.deltaX = 0
        self.deltaY = 0

        self.FOVMap = None

    def movePlayer(self, deltaX, deltaY):
        newX = self.posX + deltaX
        newY = self.posY + deltaY
        
        if (Map.instance.checkInsideBounds(newX, newY) and
           (Map.instance.getTile(newX, newY).isWalkable or Constants.ENABLE_NO_MOVEMENT_BLOCK)):

            self.posX = newX
            self.posY = newY

            return True
        else:
            return False

    def handleKeys(self, key, mouse):
        deltaX = 0
        deltaY = 0

        if key.vk == TCOD.KEY_UP or key.vk == TCOD.KEY_KP8:
            deltaY = -1

        elif key.vk == TCOD.KEY_KP9:
            deltaX = 1
            deltaY = -1
            
        elif key.vk == TCOD.KEY_RIGHT or key.vk == TCOD.KEY_KP6:
            deltaX = 1

        elif key.vk == TCOD.KEY_KP3:
            deltaX = 1
            deltaY = 1
            
        elif key.vk == TCOD.KEY_DOWN or key.vk == TCOD.KEY_KP2:
            deltaY = 1

        elif key.vk == TCOD.KEY_KP1:
            deltaX = -1
            deltaY = 1
            
        elif key.vk == TCOD.KEY_LEFT or key.vk == TCOD.KEY_KP4:
            deltaX = -1

        elif key.vk == TCOD.KEY_KP7:
            deltaX = -1
            deltaY = -1

        elif key.vk == TCOD.KEY_KP5: #Pass turn
            return 10
            
        elif key.text == b">":
            if Map.instance.getTileInt(Player.instance.getPosX(), Player.instance.getPosY()) == Tiles.STAIRS:
                Map.instance = Map.instance = Map(Constants.MAP_WIDTH, Constants.MAP_HEIGHT, Map.instance.level + 1)
                while True:
                    randX = random.randint(0, Constants.MAP_WIDTH - 1)
                    randY = random.randint(0, Constants.MAP_HEIGHT - 1)
                    if Map.instance.getTile(randX, randY).isWalkable:
                        Player.instance.posX = randX
                        Player.instance.posY = randY
                        break
                return 100

        if deltaX != 0 or deltaY != 0:
            if self.movePlayer(deltaX, deltaY):
                return 100

        return 0 #If no action was taken/action requires no ticks return 0. AKA do next action
        
    def getPosX(self):
        return self.posX

    def getPosY(self):
        return self.posY
        
    def update(self):
        self.FOVMap = Map.instance.TCODMap
        TCOD.map_compute_fov(self.FOVMap, self.posX, self.posY, self.sightRadius, True, TCOD.FOV_PERMISSIVE_2)
        
    def drawPlayer(self, cameraInstance):
        TCOD.console_put_char(0, cameraInstance.getOffsetX(self.posX), cameraInstance.getOffsetY(self.posY), '@', TCOD.BKGND_NONE)
