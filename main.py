from src.Camera import Camera
from src.Map.Map import Map, Tiles
from src.Entities.Living.Player import Player

import libtcodpy as TCOD

from time import sleep
import random

ENABLE_NO_FOV = False
ENABLE_ROOM_DEBUG = False
ENABLE_NO_MOVEMENT_BLOCK = False

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60

GUI_WIDTH = 25
GUI_HEIGHT = 5

#Game width and height should be an odd number so that the Player.instance is perfectly centered instead 1 off to the side
GAME_WIDTH = SCREEN_WIDTH - GUI_WIDTH
GAME_HEIGHT = SCREEN_HEIGHT - GUI_HEIGHT

MAP_WIDTH = 128  # Temporary values
MAP_HEIGHT = 128

fpsLimit = 60


def loadConfig():
    fontName = "terminal8x8_gs_ro.png"

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
    

def initGame():
    loadConfig()

    Map.instance = Map(MAP_WIDTH, MAP_HEIGHT, 1)
    Camera.instance = Camera(0, 0)
    while True:
        randX = random.randint(0, MAP_WIDTH - 1)
        randY = random.randint(0, MAP_HEIGHT - 1)
        if Map.instance.getTile(randX, randY).isWalkable:
            Player.instance = Player(randX, randY)
            break


def handleKeys():
    passTurn = False
    moveAction = False
    
    didAction = False #Loop and ask the Player.instance for keys until the Player.instance takes an action
    
    while not didAction:
        deltaX = 0
        deltaY = 0

        key = TCOD.Key()
        mouse = TCOD.Mouse()
        while True:
            TCOD.sys_check_for_event(TCOD.EVENT_KEY_PRESS | TCOD.EVENT_MOUSE, key, mouse)
            if key.vk != TCOD.KEY_NONE:
                break
            sleep(1 / fpsLimit)
        
        if key.vk == TCOD.KEY_ENTER and key.lalt:
            #Alt+Enter: toggle fullscreen
            TCOD.console_set_fullscreen(not TCOD.console_is_fullscreen())
            
        elif key.vk == TCOD.KEY_ESCAPE:
            return True  #exit game

        if key.c == ord('r'):
            Map.instance.regenerateMap()
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
            
        elif key.text == b">":
            if Map.instance.getTileInt(Player.instance.getPosX(), Player.instance.getPosY()) == Tiles.STAIRS:
                Map.instance = Map.instance = Map(MAP_WIDTH, MAP_HEIGHT, Map.instance.level + 1)
                while True:
                    randX = random.randint(0, MAP_WIDTH - 1)
                    randY = random.randint(0, MAP_HEIGHT - 1)
                    if Map.instance.getTile(randX, randY).isWalkable:
                        Player.instance.posX = randX
                        Player.instance.posY = randY
                        break
                moveAction = True
            
        if moveAction:
            didAction = Player.instance.movePlayer(Map.instance, deltaX, deltaY, ENABLE_NO_MOVEMENT_BLOCK)
        elif passTurn:
            didAction = True
        
    
def updateEntities():
    Player.instance.updatePlayer(Map.instance)
    Camera.instance.updatePositionFromCoordinates(Player.instance.getPosX(), Player.instance.getPosY(), MAP_WIDTH, MAP_HEIGHT, GAME_WIDTH, GAME_HEIGHT)
    
    
def updateGame():
    updateEntities()

    
def drawMap():
    rangeXStart = 0
    rangeXStop = 0
    rangeYStart = 0
    rangeYStop = 0
    
    if Map.instance.checkInsideBounds(GAME_WIDTH, GAME_HEIGHT):
        rangeXStart = Camera.instance.getPosX()
        rangeXStop = Camera.instance.getPosX() + GAME_WIDTH
        rangeYStart = Camera.instance.getPosY()
        rangeYStop = Camera.instance.getPosY() + GAME_HEIGHT
    else:
        rangeXStop = Map.instance.mapWidth
        rangeYStop = Map.instance.mapHeight
        
    for x in range(rangeXStart, rangeXStop):
        for y in range(rangeYStart, rangeYStop):
            if TCOD.map_is_in_fov(Player.instance.FOVMap, x, y) or ENABLE_NO_FOV:
                tile = Map.instance.getTile(x, y)
                TCOD.console_put_char_ex(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y),
                                         tile.char, tile.fColor, tile.bColor)
                Map.instance.seenMapArray[x][y] = True
            else:
                if Map.instance.seenMapArray[x][y]:
                    tile = Map.instance.getTile(x, y)
                    TCOD.console_put_char_ex(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y),
                                             tile.char, tile.fColor * 0.5, tile.bColor * 0.5)
            if ENABLE_ROOM_DEBUG:
                if Map.instance.checkIfCellIsInsideRoom(x, y) != -1:
                    TCOD.console_set_char_background(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y), TCOD.dark_orange)
                if Map.instance.checkIfCellIsInsideCorridor(x, y) != -1:
                    TCOD.console_set_char_background(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y), TCOD.dark_yellow)
                
                
def drawGUI():
    TCOD.console_print(0, GAME_WIDTH, 1, "Pos X: " + str(Player.instance.getPosX()))
    TCOD.console_print(0, GAME_WIDTH, 2, "Pos Y: " + str(Player.instance.getPosY()))
    TCOD.console_print(0, GAME_WIDTH, 4, "Cam X: " + str(Camera.instance.getPosX()))
    TCOD.console_print(0, GAME_WIDTH, 5, "Cam Y: " + str(Camera.instance.getPosY()))
    TCOD.console_print(0, GAME_WIDTH, 7, "Ext X: " + str(Map.instance.exitX))
    TCOD.console_print(0, GAME_WIDTH, 8, "Ext Y: " + str(Map.instance.exitY))
    TCOD.console_print(0, GAME_WIDTH, 10, "Level: " + str(Map.instance.level))
    TCOD.console_print(0, GAME_WIDTH, 12, "Turn " + str(Player.instance.turnsAlive))

    
def drawEntities():
    Player.instance.drawPlayer(Camera.instance)

    
def drawGame():
    TCOD.console_clear(0)
    
    drawMap()
    drawGUI()
    drawEntities()
    
    TCOD.console_flush()

    
#Main
initGame()

while not TCOD.console_is_window_closed():
    updateGame()
    drawGame()
    
    if handleKeys():
        break
