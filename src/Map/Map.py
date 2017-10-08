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
    STAIRS = 5

    
class TilePropertiesClass: #A structure for the static property of a tile
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
    TilePropertiesClass("Empty", '*', False),
    TilePropertiesClass("Floor", '.', True),
    TilePropertiesClass("Wall", '#', False),
    TilePropertiesClass("Closed Door", '+', False),
    TilePropertiesClass("Open Door", '/', True),
    TilePropertiesClass("Stairs", '>', True),
]


class Map:
    instance = None #Since we disallow backtracking we only need to store 1 map
    
    def __init__(self, mapWidth, mapHeight, level, minRoomWidth=5, minRoomHeight=5, maxRoomWidth=25, maxRoomHeight=25, mapSeed=None):
        
        self.mapWidth = mapWidth
        self.mapHeight = mapHeight
        self.minRoomWidth = minRoomWidth
        self.minRoomHeight = minRoomHeight
        self.maxRoomWidth = maxRoomWidth
        self.maxRoomHeight = maxRoomHeight
        self.mapSeed = mapSeed

        self.mapGenRand = None

        self.roomList = []
        self.corridorList = []

        self.level = level

        self.exitX = 0
        self.exitY = 0
        
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
        while True:
            randX = TCOD.random_get_int(self.mapGenRand, 0, self.mapWidth - 1)
            randY = TCOD.random_get_int(self.mapGenRand, 0, self.mapHeight - 1)
            
            if self.getTileInt(randX, randY) == Tiles.FLOOR:
                self.mapArray[randX][randY] = Tiles.STAIRS
                self.exitX = randX
                self.exitY = randY
                break

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
                if self.checkIfAreaIsInsideArea(node.x + node.w / 2, node.y + node.h / 2, 0, 0,
                                                roomX, roomY, roomWidth, roomHeight):
                    break

            self.roomList.append(Room(roomX, roomY, roomWidth, roomHeight))
            self.roomList[-1].generateEmptyRoom(self.mapArray) #[-1] means get last element
        else:
            #To create the paths, simply make a path from the center of each node
            pathSize = 1
            
            centerLX = TCOD.bsp_left(node).x + round(int(TCOD.bsp_left(node).w / 2))
            centerLY = TCOD.bsp_left(node).y + round(int(TCOD.bsp_left(node).h / 2))
            centerRX = TCOD.bsp_right(node).x + round(int(TCOD.bsp_right(node).w / 2))
            centerRY = TCOD.bsp_right(node).y + round(int(TCOD.bsp_right(node).h / 2))

            horizontalPath = True

            if centerLY < centerRY:
                horizontalPath = False

            corridorX = 0
            corridorY = 0
            corridorWidth = 0
            corridorHeight = 0

            if horizontalPath:
                corridorX = centerLX - 1
                corridorY = centerLY - int(math.ceil(pathSize / 2))
                corridorWidth = centerRX - centerLX + 2 #We add 1 because there is 1 wall in the way when connecting to another corridor
                corridorHeight = pathSize + 2 #We add 2 because there are 2 walls we generate
            else:
                corridorX = centerLX - int(math.ceil(pathSize / 2))
                corridorY = centerLY - 1
                corridorWidth = pathSize + 2
                corridorHeight = centerRY - centerLY + 2
                
            self.corridorList.append(Corridor(corridorX, corridorY, corridorWidth, corridorHeight, horizontalPath))
            self.corridorList[-1].generateEmptyCorridor(self.mapArray) #[-1] means get last element

        return True

    def revealMap(self, includingEmptyTiles=True):
        if includingEmptyTiles:
            self.seenMapArray = [[True for _ in range(self.mapWidth)] for _ in range(self.mapHeight)]
        else:
            for x in range(self.mapWidth):
                for y in range(self.mapHeight):
                    if not self.mapArray[x][y] == Tiles.EMPTY:
                        self.seenMapArray[x][y] = True
                        
    def regenerateMap(self):
        self.__generateMap()

    def getTileInt(self, posX, posY):
        return self.mapArray[posX][posY]
        
    def getTile(self, posX, posY):
        return tileProperties[self.mapArray[posX][posY]]
    
    def getTCODMap(self):
        return self.TCODMap
    
    def checkInsideBounds(self, posX, posY):
        return posX >= 0 and posY >= 0 and posX < self.mapWidth and posY < self.mapHeight

    def checkIfAreaIsInsideArea(self, AX, AY, AW, AH, BX, BY, BW, BH):
        if AX + AW < BX + BW and AX > BX and AY > BY and AY + AH < BY + BH:
            return True
        return False

    def checkIfCellIsInsideRoom(self, posX, posY):
        for i, room in enumerate(self.roomList):
            if self.checkIfAreaIsInsideArea(posX, posY, 0, 0, room.posX - 1, room.posY - 1, room.width + 1, room.height + 1):
                return i
        return -1 #If there are no rooms containing this cell, return -1

    def checkIfCellIsInsideCorridor(self, posX, posY):
        for i, corridor in enumerate(self.corridorList):
            if self.checkIfAreaIsInsideArea(posX, posY, 0, 0, corridor.posX - 1, corridor.posY - 1, corridor.width + 1, corridor.height + 1):
                return i
        return -1 #If there are no corridors containing this cell, return -1

    
class Room:
    def __init__(self, posX, posY, width, height):
        self.posX = posX
        self.posY = posY
        self.width = width
        self.height = height

    def generateEmptyRoom(self, mapArray):
        for x in range(self.posX, self.posX + self.width):
            for y in range(self.posY, self.posY + self.height):
                if x == self.posX or y == self.posY or x == self.posX + self.width - 1 or y == self.posY + self.height - 1:
                    mapArray[x][y] = Tiles.WALL
                else:
                    mapArray[x][y] = Tiles.FLOOR

    
class Corridor:
    def __init__(self, posX, posY, width, height, isHorizontal):
        self.posX = posX
        self.posY = posY
        self.width = width
        self.height = height
        self.isHorizontal = isHorizontal

    def generateEmptyCorridor(self, mapArray):
        for x in range(self.posX, self.posX + self.width):
            for y in range(self.posY, self.posY + self.height):
                if x == self.posX or y == self.posY or x == self.posX + self.width - 1 or y == self.posY + self.height - 1:
                    if mapArray[x][y] == Tiles.EMPTY:
                        mapArray[x][y] = Tiles.WALL
                else:
                    mapArray[x][y] = Tiles.FLOOR
