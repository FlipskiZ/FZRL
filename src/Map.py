from enum import IntEnum
import math
from time import time

import libtcodpy as TCOD


class Tiles(IntEnum): #Tiles that appear on the map, the terrain
    EMPTY = 0
    FLOOR = 1
    WALL = 2
    CLOSED_DOOR = 3
    OPEN_DOOR = 4

    
class TilePropertiesClass:
    def __init__(self, name, char, isWalkable, isTransparent=None, fColor=TCOD.white, bColor=TCOD.black):
        self.name = name
        self.char = char
        self.isWalkable = isWalkable
        if isTransparent is None:
            self.isTransparent = self.isWalkable
        self.fColor = fColor
        self.bColor = bColor


#(Tile name, Printed character, Can walk on, Can see through, Character color, Background color)
tileProperties = [
    TilePropertiesClass("Empty", ' ', False),
    TilePropertiesClass("Floor", '.', True),
    TilePropertiesClass("Wall", '#', False),
    TilePropertiesClass("Closed Door", '+', False),
    TilePropertiesClass("Open Door", '/', True),
]


class MapClass:
    mapLevelsList = [] #A list of all the map level instances. index 0 is level 1, index 10 is level 11, etc.
    
    def __init__(self, mapWidth, mapHeight, minRoomWidth=5, minRoomHeight=5, maxRoomWidth=25, maxRoomHeight=25, mapSeed=None):
        self.mapWidth = mapWidth
        self.mapHeight = mapHeight
        self.minRoomWidth = minRoomWidth
        self.minRoomHeight = minRoomHeight
        self.maxRoomWidth = maxRoomWidth
        self.maxRoomHeight = maxRoomHeight
        self.mapSeed = mapSeed

        self.mapGenRand = None
        
        self.__generateMap()

    def __generateOutdoorMap(self):
        for x in range(self.mapWidth):
            for y in range(self.mapHeight):
                if TCOD.random_get_int(self.mapGenRand, 0, 9) == 0:
                    self.mapArray[x][y] = Tiles.WALL
                else:
                    self.mapArray[x][y] = Tiles.FLOOR
        #Outdoor generation test
        
    def __generateMap(self):
        self.mapArray = [[0 for _ in range(self.mapHeight)] for _ in range(self.mapWidth)] #Create an empty 2D map array
        self.seenMapArray = [[False for _ in range(self.mapWidth)] for _ in range(self.mapHeight)]
        
        #Initilize the random generator from a seed, if any, otherwise use the current time as the seed
        if self.mapGenRand is None:
            if not self.mapSeed:
                self.mapSeed = int(round(time()))
            self.mapGenRand = TCOD.random_new_from_seed(self.mapSeed)
        
        #""" #BSP Dungeon generation outcommenting

        self.BSPTree = TCOD.bsp_new_with_size(0, 0, self.mapWidth, self.mapHeight)

        #So we get the average iterations needed to create our desired sized, this is so the amount of rooms scales with the room sizes and map sizes.
        self.BSPIterations = int(round(math.log((self.mapHeight + self.mapWidth) / 2, 2) -
                                       math.log((self.maxRoomWidth + self.maxRoomHeight) / 2, 2)))
        self.BSPIterations *= 3 #This is so we get more rooms, and the dungeon is more compact
        
        #(node, randomizer, max iterations, smallest height, smallest width, max height to width ratio, max width to height ratio)
        TCOD.bsp_split_recursive(self.BSPTree, self.mapGenRand, self.BSPIterations,
                                 self.minRoomWidth, self.minRoomHeight, 2, 2)

        #Traverses the level from bottom to top, this way we can simply draw rooms and corridors and be safe that things are overwritten as they are supposed to.
        TCOD.bsp_traverse_inverted_level_order(self.BSPTree, self.__processBSPNode, 0)

        #Rest of the generation

        #""" #BSP Dungeon generation outcommenting

        self.TCODMap = TCOD.map_new(self.mapHeight, self.mapWidth) #Create a TCOD map, neccesary for some TCOD functions.
        
        for x in range(self.mapWidth):
            for y in range(self.mapHeight):
                TCOD.map_set_properties(self.TCODMap, x, y, self.getTile(x, y).isTransparent, self.getTile(x, y).isWalkable)

    def __processBSPNode(self, node, userData):
        """for x in range(node.x, node.x + node.w): #Draw the whole tree
            for y in range(node.y, node.y + node.h):
                if x == node.x or y == node.y or x == self.mapWidth - 1 or y == self.mapHeight - 1:
                    self.mapArray[x][y] = Tiles.DOOR"""
        
        if TCOD.bsp_is_leaf(node):
            minRatioOfNode = 1.5
            
            maxRoomWidth = self.maxRoomWidth
            maxRoomHeight = self.maxRoomHeight
            minRoomWidth = int(round(node.w / minRatioOfNode))
            minRoomHeight = int(round(node.h / minRatioOfNode))
            
            if node.w < self.maxRoomWidth:
                maxRoomWidth = node.w
            if node.h < self.maxRoomHeight:
                maxRoomHeight = node.h

            if minRoomWidth < self.minRoomWidth:
                minRoomWidth = self.minRoomWidth
            if minRoomHeight < self.minRoomHeight:
                minRoomHeight = self.minRoomHeight

            if minRoomWidth > maxRoomWidth:
                minRoomWidth = maxRoomWidth
            if minRoomHeight > maxRoomHeight:
                minRoomHeight = maxRoomHeight

            roomX = 0
            roomY = 0

            roomWidth = 0
            roomHeight = 0

            roomWidth = TCOD.random_get_int(self.mapGenRand, minRoomWidth, maxRoomWidth)
            roomHeight = TCOD.random_get_int(self.mapGenRand, minRoomHeight, maxRoomHeight)
            
            while True:
                roomX = TCOD.random_get_int(self.mapGenRand, node.x, node.x + node.w - roomWidth)
                roomY = TCOD.random_get_int(self.mapGenRand, node.y, node.y + node.h - roomHeight)

                #We make sure that the center cell of the node is inside the room
                if self.checkIfAreaIsInsideArea(node.x + node.w / 2, node.y + node.h / 2, 1, 1,
                                                roomX, roomY, roomWidth, roomHeight):
                    break
                
            for x in range(roomX, roomX + roomWidth):
                for y in range(roomY, roomY + roomHeight):
                    if x == roomX or y == roomY or x == roomX + roomWidth - 1 or y == roomY + roomHeight - 1:
                        self.mapArray[x][y] = Tiles.WALL
                    else:
                        self.mapArray[x][y] = Tiles.FLOOR

            #We store the room values in the node, so that we may easily retrieve it in the future
            node.roomWidth = roomWidth
            node.roomHeight = roomHeight

            node.roomX = roomX
            node.roomY = roomY
        else:
            #To create the paths, simply make a path from the center of each node
            pathSize = 1 #Actual size of path will be (pathSize-1)*2 + 1
            
            centerLX = TCOD.bsp_left(node).x + round(int(TCOD.bsp_left(node).w / 2))
            centerLY = TCOD.bsp_left(node).y + round(int(TCOD.bsp_left(node).h / 2))
            centerRX = TCOD.bsp_right(node).x + round(int(TCOD.bsp_right(node).w / 2))
            centerRY = TCOD.bsp_right(node).y + round(int(TCOD.bsp_right(node).h / 2))

            horizontalPath = True

            if centerLY < centerRY:
                horizontalPath = False

            if horizontalPath:
                for x in range(centerLX, centerRX + 1):
                    for y in range(centerLY - pathSize, centerLY + pathSize + 1): #The center y values will be the same of both nodes
                        if x == centerLX or y == centerLY - pathSize or x == centerRX or y == centerLY + pathSize:
                            if self.mapArray[x][y] != Tiles.FLOOR:
                                self.mapArray[x][y] = Tiles.WALL
                        else:
                            self.mapArray[x][y] = Tiles.FLOOR
            else:
                for x in range(centerLX - pathSize, centerLX + pathSize + 1): #The center x values will be the same of both nodes
                    for y in range(centerLY, centerRY + 1):
                        if x == centerLX - pathSize or y == centerLY or x == centerLX + pathSize or y == centerRY:
                            if self.mapArray[x][y] != Tiles.FLOOR:
                                self.mapArray[x][y] = Tiles.WALL
                        else:
                            self.mapArray[x][y] = Tiles.FLOOR
                
        return True

    def regenerateMap(self):
        self.__generateMap()
        
    def getTile(self, posX, posY):
        return tileProperties[self.mapArray[posX][posY]]

    def getTCODMap(self):
        return self.TCODMap
    
    def checkInsideBounds(self, posX, posY):
        return posX >= 0 and posY >= 0 and posX < self.mapWidth and posY < self.mapHeight

    def checkIfAreaIsInsideArea(self, BX, BY, BW, BH, AX, AY, AW, AH):
        if BX + BW < AX + AW and BX > AX and BY > AY and BY + BH < AY + AH:
            return True
        return False
