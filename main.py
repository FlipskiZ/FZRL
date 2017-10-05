from src.Camera import CameraClass
from src.Map import MapClass, Tiles
from src.Player import PlayerClass

import libtcodpy as TCOD

from time import sleep
import random

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60

GUI_WIDTH = 25
GUI_HEIGHT = 5

#Game width and height should be an odd number so that the playerInstance is perfectly centered instead 1 off to the side
GAME_WIDTH = SCREEN_WIDTH - GUI_WIDTH
GAME_HEIGHT = SCREEN_HEIGHT - GUI_HEIGHT

MAP_WIDTH = 128  # Temporary values
MAP_HEIGHT = 128


def loadConfig():
    fontName = "terminal8x8_gs_ro.png"
    fpsLimit = 60

    cFile = open("config/config.ini") #Open up the configuration file in read only mode

    for line in cFile:
        line = line.replace(' ', '').replace("\n", '')
        if '=' in line:
            line = line.split('=', 1)
            line[0] = line[0].lower()
            if line[0].startswith("font"):
                fontName = line[1]
            elif line[0].startswith("fps"):
                fpsLimit = int(line[1])

    cFile.close()

    TCOD.sys_set_fps(fpsLimit)
    TCOD.console_set_custom_font("fonts/" + fontName, TCOD.FONT_TYPE_GREYSCALE | TCOD.FONT_LAYOUT_ASCII_INROW)

    TCOD.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'FZRL', False)

    sleep(0.02) #Workaround for empty screen at launch
    
    TCOD.console_set_default_background(0, TCOD.black)
    TCOD.console_set_default_foreground(0, TCOD.white)

    
loadConfig()


def handleKeys():
    passTurn = False
    moveAction = False
    
    didAction = False #Loop and ask the playerInstance for keys until the playerInstance takes an action
    
    while not didAction:
        deltaX = 0
        deltaY = 0

        key = TCOD.console_wait_for_keypress(True)
        
        if key.vk == TCOD.KEY_ENTER and key.lalt:
            #Alt+Enter: toggle fullscreen
            TCOD.console_set_fullscreen(not TCOD.console_is_fullscreen())
            
        elif key.vk == TCOD.KEY_ESCAPE:
            return True  #exit game

        if key.c == ord('r'):
            MapClass.mapLevelsList[0].regenerateMap()
            passTurn = True
        
        #movement keys
        elif key.vk == TCOD.KEY_UP or key.vk == TCOD.KEY_KP8:
            deltaY = -1
            moveAction = True

        elif key.vk == TCOD.KEY_KP9:
            deltaX = 1
            deltaY = -1
            moveAction = True
            
        elif key.vk == TCOD.KEY_RIGHT or key.vk == TCOD.KEY_KP6:
            deltaX = 1
            moveAction = True

        elif key.vk == TCOD.KEY_KP3:
            deltaX = 1
            deltaY = 1
            moveAction = True
            
        elif key.vk == TCOD.KEY_DOWN or key.vk == TCOD.KEY_KP2:
            deltaY = 1
            moveAction = True

        elif key.vk == TCOD.KEY_KP1:
            deltaX = -1
            deltaY = 1
            moveAction = True
            
        elif key.vk == TCOD.KEY_LEFT or key.vk == TCOD.KEY_KP4:
            deltaX = -1
            moveAction = True

        elif key.vk == TCOD.KEY_KP7:
            deltaX = -1
            deltaY = -1
            moveAction = True

        elif key.vk == TCOD.KEY_KP5: #Pass turn
            passTurn = True
            
        if moveAction:
            didAction = playerInstance.movePlayer(MapClass.mapLevelsList[0], deltaX, deltaY)
        elif passTurn:
            didAction = True

            
def updateEntities():
    playerInstance.updatePlayer(MapClass.mapLevelsList[0])
    cameraInstance.updatePositionFromCoordinates(playerInstance.getPosX(), playerInstance.getPosY(), MAP_WIDTH, MAP_HEIGHT, GAME_WIDTH, GAME_HEIGHT)
    
    
def updateGame():
    updateEntities()

    
def drawMap():
    rangeXStart = 0
    rangeXStop = 0
    rangeYStart = 0
    rangeYStop = 0
    
    if MapClass.mapLevelsList[0].checkInsideBounds(GAME_WIDTH, GAME_HEIGHT):
        rangeXStart = cameraInstance.getPosX()
        rangeXStop = cameraInstance.getPosX() + GAME_WIDTH
        rangeYStart = cameraInstance.getPosY()
        rangeYStop = cameraInstance.getPosY() + GAME_HEIGHT
    else:
        rangeXStop = MapClass.mapLevelsList[0].mapWidth
        rangeYStop = MapClass.mapLevelsList[0].mapHeight
        
    for x in range(rangeXStart, rangeXStop):
        for y in range(rangeYStart, rangeYStop):
            if TCOD.map_is_in_fov(playerInstance.FOVMap, x, y):
                tile = MapClass.mapLevelsList[0].getTile(x, y)
                TCOD.console_put_char_ex(0, cameraInstance.getOffsetX(x), cameraInstance.getOffsetY(y),
                                         tile.char, tile.fColor, tile.bColor)
                MapClass.mapLevelsList[0].seenMapArray[x][y] = True
            else:
                if MapClass.mapLevelsList[0].seenMapArray[x][y]:
                    tile = MapClass.mapLevelsList[0].getTile(x, y)
                    TCOD.console_put_char_ex(0, cameraInstance.getOffsetX(x), cameraInstance.getOffsetY(y),
                                             tile.char, tile.fColor * 0.5, tile.bColor * 0.5)

                
def drawGUI():
    TCOD.console_print(0, GAME_WIDTH, 1, "Pos X: " + str(playerInstance.getPosX()))
    TCOD.console_print(0, GAME_WIDTH, 2, "Pos Y: " + str(playerInstance.getPosY()))
    TCOD.console_print(0, GAME_WIDTH, 4, "Cam X: " + str(cameraInstance.getPosX()))
    TCOD.console_print(0, GAME_WIDTH, 5, "Cam Y: " + str(cameraInstance.getPosY()))
    TCOD.console_print(0, GAME_WIDTH, 7, "Turn " + str(playerInstance.turnsAlive))

    
def drawEntities():
    playerInstance.drawPlayer(cameraInstance)

    
def drawGame():
    TCOD.console_clear(0)
    
    drawMap()
    drawGUI()
    drawEntities()

    TCOD.console_flush()

    
MapClass.mapLevelsList.append(MapClass(MAP_WIDTH, MAP_HEIGHT))

while True:
    randX = random.randint(0, MAP_WIDTH - 1)
    randY = random.randint(0, MAP_HEIGHT - 1)
    if MapClass.mapLevelsList[0].getTile(randX, randY).isWalkable:
        playerInstance = PlayerClass(randX, randY)
        break

cameraInstance = CameraClass(0, 0)

while not TCOD.console_is_window_closed():
    updateGame()
    drawGame()
    
    #handle keys and exit game if needed
    exit = handleKeys()
    if exit:
        break
