import libtcodpy as TCOD


class PlayerClass:
    def __init__(self, posX, posY, sightRadius=0):
        self.turnsAlive = 0

        self.posX = posX
        self.posY = posY

        self.sightRadius = sightRadius #0 is unlimited
        
        self.deltaX = 0
        self.deltaY = 0

        self.FOVMap = None

    def movePlayer(self, mapInstance, deltaX, deltaY):
        newX = self.posX + deltaX
        newY = self.posY + deltaY
        
        if (mapInstance.checkInsideBounds(newX, newY) and
           mapInstance.getTile(newX, newY).isWalkable):

            self.posX = newX
            self.posY = newY

            return True
        else:
            return False
            
    def getPosX(self):
        return self.posX

    def getPosY(self):
        return self.posY
        
    def updatePlayer(self, mapInstance):
        self.turnsAlive += 1

        self.FOVMap = mapInstance.TCODMap
        TCOD.map_compute_fov(self.FOVMap, self.posX, self.posY, self.sightRadius, True, TCOD.FOV_PERMISSIVE_2)
        
    def drawPlayer(self, cameraInstance):
        TCOD.console_put_char(0, cameraInstance.getOffsetX(self.posX), cameraInstance.getOffsetY(self.posY), '@', TCOD.BKGND_NONE)
