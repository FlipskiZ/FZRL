class CameraClass:
    def __init__(self, posX, posY):
        self.cameraPosX = posX
        self.cameraPosY = posY

    def updatePositionFromCoordinates(self, playerPosX, playerPosY, mapWidth, mapHeight, gameWidth, gameHeight):
        self.cameraPosX = playerPosX - int(gameWidth / 2)
        self.cameraPosY = playerPosY - int(gameHeight / 2)

        if playerPosX < int(gameWidth / 2):
            self.cameraPosX = 0
        if playerPosY < int(gameHeight / 2):
            self.cameraPosY = 0

        if playerPosX >= mapWidth - int(gameWidth / 2):
            self.cameraPosX = mapWidth - gameWidth
        if playerPosY >= mapHeight - int(gameHeight / 2):
            self.cameraPosY = mapHeight - gameHeight

        if self.cameraPosX < 0:
            self.cameraPosX = 0
        if self.cameraPosY < 0:
            self.cameraPosY = 0
        
    def getPosX(self):
        return self.cameraPosX
    
    def getPosY(self):
        return self.cameraPosY

    def getOffsetX(self, posX):
        return posX - self.getPosX()

    def getOffsetY(self, posY):
        return posY - self.getPosY()
