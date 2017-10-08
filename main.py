from src.Camera import Camera
from src.Map.Map import Map
from src.Entities.Living.Player import Player
from src import Time

from src import Constants
from src import Stats

import libtcodpy as TCOD

from time import sleep
import math
import random


exitGame = False


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
                FPS_LIMIT = int(line[1])

    cFile.close()

    TCOD.sys_set_fps(FPS_LIMIT)
    TCOD.console_set_custom_font("fonts/" + fontName, TCOD.FONT_TYPE_GREYSCALE | TCOD.FONT_LAYOUT_ASCII_INROW)

    TCOD.console_init_root(Constants.SCREEN_WIDTH, Constants.SCREEN_HEIGHT, 'FZRL', False)

    sleep(0.02) #Workaround for empty screen at launch
    
    TCOD.console_set_default_background(0, TCOD.black)
    TCOD.console_set_default_foreground(0, TCOD.white)
    

def initGame():
    loadConfig()

    Map.instance = Map(Constants.MAP_WIDTH, Constants.MAP_HEIGHT, 1)
    Camera.instance = Camera(0, 0)
    while True:
        randX = random.randint(0, Constants.MAP_WIDTH - 1)
        randY = random.randint(0, Constants.MAP_HEIGHT - 1)
        if Map.instance.getTile(randX, randY).isWalkable:
            Player.instance = Player(randX, randY)
            break
    Time.addToQueue(Player.instance)

    #We draw the first frame, as well as the requirements for it to be drawn correctly
    Player.instance.update()
    Camera.instance.updatePositionFromCoordinates(Player.instance.getPosX(), Player.instance.getPosY(), Constants.MAP_WIDTH, Constants.MAP_HEIGHT, Constants.GAME_WIDTH, Constants.GAME_HEIGHT)
    drawGame()


def handleKeys():
    ticksTaken = 0 #Loop and ask the Player.instance for keys until the Player.instance takes an action
    
    while ticksTaken == 0:
        key = TCOD.Key()
        mouse = TCOD.Mouse()
        while True:
            TCOD.sys_check_for_event(TCOD.EVENT_KEY_PRESS | TCOD.EVENT_MOUSE, key, mouse)
            if key.vk != TCOD.KEY_NONE:
                break
            sleep(1 / Constants.FPS_LIMIT)
        
        if key.vk == TCOD.KEY_ENTER and key.lalt:
            TCOD.console_set_fullscreen(not TCOD.console_is_fullscreen())
            
        elif key.vk == TCOD.KEY_ESCAPE:
            global exitGame
            exitGame = True
            return 0

        if key.c == ord('r'):
            Map.instance.regenerateMap()
            return 0

        ticksTaken = Player.instance.handleKeys(key, mouse)
    return ticksTaken


def handleTimeQueue():
    nextEntity = Time.getNextInQueue()
    ticksTaken = 0
    if isinstance(nextEntity, Player): #If the next entity to move is the player
        ticksTaken = handleKeys()
        nextEntity.update()
    else:
        ticksTaken = nextEntity.update()
    Time.addToQueue(nextEntity, ticksTaken)
    Time.sortQueue()

    #The player could theoretically have been moved while it wasn't his turn
    Camera.instance.updatePositionFromCoordinates(Player.instance.getPosX(), Player.instance.getPosY(), Constants.MAP_WIDTH, Constants.MAP_HEIGHT, Constants.GAME_WIDTH, Constants.GAME_HEIGHT)
    
    
def updateGame():
    handleTimeQueue()

    
def drawMap():
    rangeXStart = 0
    rangeXStop = 0
    rangeYStart = 0
    rangeYStop = 0
    
    if Map.instance.checkInsideBounds(Constants.GAME_WIDTH, Constants.GAME_HEIGHT):
        rangeXStart = Camera.instance.getPosX()
        rangeXStop = Camera.instance.getPosX() + Constants.GAME_WIDTH
        rangeYStart = Camera.instance.getPosY()
        rangeYStop = Camera.instance.getPosY() + Constants.GAME_HEIGHT
    else:
        rangeXStop = Map.instance.mapWidth
        rangeYStop = Map.instance.mapHeight
        
    for x in range(rangeXStart, rangeXStop):
        for y in range(rangeYStart, rangeYStop):
            if TCOD.map_is_in_fov(Player.instance.FOVMap, x, y) or Constants.ENABLE_NO_FOV:
                tile = Map.instance.getTile(x, y)
                TCOD.console_put_char_ex(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y),
                                         tile.char, tile.fColor, tile.bColor)
                Map.instance.seenMapArray[x][y] = True
            else:
                if Map.instance.seenMapArray[x][y]:
                    tile = Map.instance.getTile(x, y)
                    TCOD.console_put_char_ex(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y),
                                             tile.char, tile.fColor * 0.5, tile.bColor * 0.5)
            if Constants.ENABLE_ROOM_DEBUG:
                insideRoom = False
                insideCorridor = False
                
                if Map.instance.checkIfCellIsInsideRoom(x, y) != -1:
                    insideRoom = True
                if Map.instance.checkIfCellIsInsideCorridor(x, y) != -1:
                    insideCorridor = True
                    
                if insideRoom and insideCorridor:
                    TCOD.console_set_char_background(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y), TCOD.dark_yellow * TCOD.dark_orange)
                elif insideCorridor:
                    TCOD.console_set_char_background(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y), TCOD.dark_yellow)
                elif insideRoom:
                    TCOD.console_set_char_background(0, Camera.instance.getOffsetX(x), Camera.instance.getOffsetY(y), TCOD.dark_orange)
                
                
def drawGUI():
    TCOD.console_print(0, Constants.GAME_WIDTH, 1, "Pos X: " + str(Player.instance.getPosX()))
    TCOD.console_print(0, Constants.GAME_WIDTH, 2, "Pos Y: " + str(Player.instance.getPosY()))
    TCOD.console_print(0, Constants.GAME_WIDTH, 4, "Cam X: " + str(Camera.instance.getPosX()))
    TCOD.console_print(0, Constants.GAME_WIDTH, 5, "Cam Y: " + str(Camera.instance.getPosY()))
    TCOD.console_print(0, Constants.GAME_WIDTH, 7, "Ext X: " + str(Map.instance.exitX))
    TCOD.console_print(0, Constants.GAME_WIDTH, 8, "Ext Y: " + str(Map.instance.exitY))
    TCOD.console_print(0, Constants.GAME_WIDTH, 10, "Level: " + str(Map.instance.level))
    #The turn and tick info is a turn delayed because it's drawn on the main screen as of right now
    TCOD.console_print(0, Constants.GAME_WIDTH, 12, "Tick " + str(Stats.ticksProgressed))
    TCOD.console_print(0, Constants.GAME_WIDTH, 13, "Turn " + str(math.floor(Stats.ticksProgressed / 100)))


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

while not TCOD.console_is_window_closed() and not exitGame:
    updateGame()
    drawGame()


#When exiting save game/go to the menu/show a dialog to the player
