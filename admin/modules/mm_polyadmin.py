# -*- coding: cp1252 -*-
import bf2, host, mm_utils, math, bf2.PlayerManager, datetime, os, sys
from bf2.stats.constants import *


# Module information #
__version__ = "0.4"
__required_modules__ = {
	'modmanager': 2.0
}
__supported_games__ = {
	'bf2': True
}
__supports_reload__ = True
__description__ = "PolyAdmin AutoAdmin Module v%s" % __version__

__author__ = "ArmedGuy from Pie-Studios"
settings = {
    "dalian_plant": ["us_safebase.sb","ch_safebase.sb"]
}
# Modmanager constant #
mm = None


# Dev mode #
dev = True
# Code #
def mm_load( modManager ):
	return PolyAdmin( modManager, settings)
    
    
    
class PolyAdmin(object):
    _settings = {}
    _state = 0
    _areas = None
    _newPoly = None
    def __init__(self, modManager, settings):
        globals()["mm"] = modManager
        self._settings = settings
        self._areas = []
        self._newPoly = {}
        
        
    def init( self ):
        if 0 == self._state:
            #host.registerHandler( 'EnterVehicle', self.onEnterVehicle, 1 )
            #host.registerHandler( 'PlayerScore', self.onScore, 1 )
            host.registerHandler( 'PlayerDeath', self.onDeath, 1 )
            if dev == True:
                host.registerHandler( 'ChatMessage', self.onChat, 1 )
            #host.registerHandler( 'PlayerSpawn', self.onPlayerSpawn, 1)
            #host.registerHandler( 'PlayerConnect', self.onPlayerConnect, 1)
            #host.registerHandler( 'PlayerDisconnect', self.onPlayerDisconnect, 1)
            host.registerGameStatusHandler(self.onGameStatusChanged) 
		# Update to the running state
        self._state = 1
        
    def shutdown( self ):
        host.unregisterGameStatusHandler(self.onGameStatusChanged)
        self._state = 2

    def update( self ):
        pass
        
# Configuration loading #
    def loadAreas(self):
        mm.info("Loading areas")
        for a in self._areas:
            a.destroy()
        map = bf2.serverSettings.getMapName().lower()
        mm.info("Loading all areas for map: %s" % map)
        try:
            for area in self._settings[map]:
                try: 
                    f = open("polyadmin/%s/%s" % (map, area))
                    mm.info("Loading area: %s" % area)
                    self._areas.append(PolygonTrigger(f, self))
                except IOError:
                    mm.error("Failed to load area file %s" % area)
        except:
            mm.error("Failed to load area %s: " % area["name"],True)
            
            
# Actions #
    def killPlayer(self, player):
        vehicle = player.getVehicle()
        rootVehicle = getRootParent(vehicle)
        if getVehicleType(rootVehicle.templateName) == VEHICLE_TYPE_SOLDIER:
            rootVehicle.setDamage(0)
            # This should kill them !
        else:
            rootVehicle.setDamage(1) 
            # a vehicle will likely explode within 1 sec killing entire crew,
            # not so sure about base defenses though
        player.safebasePunish = True
        try:
            player.setTimeToSpawn(0)
        except:
            pass
# Event Handlers #
    def onGameStatusChanged(self, status):
        if status == bf2.GameStatus.Playing:
            self.loadAreas()
    def onChat(self, playerId, text, channel, flags): # TODO - ingame dev commands to create new polygons
        if self._state == 1 and dev == True and playerId != -1:
            if text[0] == "!":
                if " " in text:
                    cmd = text[1:].split(" ")
                else:
                    cmd = [text[1:]]
                self.onCommand(bf2.playerManager.getPlayerByIndex(playerId), cmd)
    def onDeath(self, player, soldier):
        if player.safebasePunish and player.safebasePunish == True:
            try:
                player.setTimeToSpawn(40)
            except:
                pass
            player.safebasePunish = False
                
    def onCommand(self, player, cmd):
        if cmd[0] == "pcreate":
            self._newPoly = {}
            self._newPoly["fname"] = ''.join(cmd[1:])
            self.broadcast("Created a new polygon object, ready to edit")
            
        if cmd[0] == "ppoint":
            if "points" not in self._newPoly:
                self._newPoly["points"] = []
            self._newPoly["points"].append(player.getDefaultVehicle().getPosition())
            self.broadcast("Added point at %s" % str(player.getDefaultVehicle().getPosition()))
            
        if cmd[0] == "psave":
            self.broadcast("About to save polygon")
            name = ' '.join(cmd[1:])
            map = bf2.serverSettings.getMapName().lower()
            self.broadcast("Got map name")
            f = open("polyadmin/%s/%s" % (map, self._newPoly["fname"]), "w")
            self.broadcast("Opened file")
            f.write("name:%s\\" % name)
            f.write("floor:-1\\height:-1\\team:%s\\interval:2" % str(player.getTeam()))
            self.broadcast("Wrote name")
            for p in self._newPoly["points"]:
                f.write("\\point:%s/%s" % (str(p[0]), str(p[2])))
            f.close()
            self.broadcast("Saved polygon")
            
        if cmd[0] == "pinfo":
            for obj in self._newPoly:
                self.broadcast("%s: %s" % (str(obj), str(self._newPoly[obj])))
            
    def onSafebase(self, polygon, player):
        if player.isAlive():
            player.score.score -= 5
            self.killPlayer(player)
            self.broadcast("%s has punished for violating the no-safebase rules. Entered %s" % (player.getName(), polygon.name))
        else:
            pass
        
        
        
# Extra stuff #
    def broadcast(self, msg):
        host.rcon_invoke("game.sayAll \"" + str(msg) + "\"")
        #host.sgl_sendTextMessage(-1, 12, 2, msg, 0)
class PolygonTrigger:
    name = ""
    polygon = None
    floor = -1
    height = -1
    team = -1
    interval = 5
    timer = None
    callback = None
    def __init__(self, file, callbackClass): # already assured it exists, opened for reading
        self.polygon = Polygon2D()
        for line in file.readlines()[0].split("\\"):
            if ":" in line:
                s = line.strip().split(":")
                if s[0] == "name":
                    self.name = s[1]
                    mm.info("PolygonTrigger name: %s" % s[1])
                if s[0] == "floor":
                    self.floor = int(s[1])
                    mm.info("PolygonTrigger floor: %s" % s[1])
                if s[0] == "height":
                    self.height = int(s[1])
                    mm.info("PolygonTrigger height: %s" % s[1])
                if s[0] == "team":
                    self.team = int(s[1])
                    mm.info("PolygonTrigger team: %s" % s[1])
                if s[0] == "interval":
                    self.interval = int(s[1])
                    mm.info("PolygonTrigger interval: %s" % s[1])
                if s[0] == "callback":
                    self.callback = getattr(callbackClass, s[1])
                    mm.info("PolygonTrigger callback: callbackClass.%s" % s[1])
                if s[0] == "point":
                    xy = s[1].split("/")
                    self.polygon.add(Point(float(xy[0]),float(xy[1])))
                    mm.info("PolygonTrigger point: %s,%s" % (str(self.polygon._coords[-1].x),str(self.polygon._coords[-1].y)))
        file.close()
        self.polygon.precalculate()
        self.timer = bf2.Timer(self.onTick, self.interval, 1, ())
        self.timer.setRecurring(self.interval)
        
    def destroy(self):
        if self.timer != None:
            self.timer.destroy()
            self.timer = None
    
    def isPlayerInside(self, player):
        if player != None and player.isAlive():
            try:
                vehicle = player.getDefaultVehicle()
                pos = vehicle.getPosition()
                if self.floor != -1:
                    if self.floor < pos[1]:
                        if self.height != -1:
                            if self.height > pos[1] and self.polygon.isXYInside(pos[0], pos[2]) and self.callback: self.callback(self, player)
                        else:
                            if self.polygon.isXYInside(pos[0], pos[2]) and self.callback: self.callback(self, player)
                else:
                    if self.polygon.isXYInside(pos[0], pos[2]): 
                        if(self.callback): self.callback(self, player)
            except:
                mm.error("isPlayerInside failed as well failed, damn these errors", True)
        
    def onTick(self, data):
        for player in bf2.playerManager.getPlayers():
            if player.isAlive():
                try:
                    if self.team == -1 or self.team == player.getTeam():
                        vehicle = player.getDefaultVehicle()
                        pos = vehicle.getPosition()
                        if self.floor != -1:
                            if self.floor < pos[1]:
                                if self.height != -1:
                                    if self.height > pos[1] and self.polygon.isXYInside(pos[0], pos[2]) and self.callback: self.callback(self, player)
                                else:
                                    if self.polygon.isXYInside(pos[0], pos[2]) and self.callback: self.callback(self, player)
                        else:
                            if self.polygon.isXYInside(pos[0], pos[2]): 
                                if(self.callback): self.callback(self, player)
                except:
                    mm.error("onTick failed, damn these errors", True)
        
# Maths for polygon calculation #
class Point:
    x = 0
    y = 0
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Line:
    p1 = None
    p2 = None
    def __init__(self, puno, pdoez): # i cant speak spanish
        self.p1 = puno
        self.p2 = pdoez

class Polygon2D:
    _coords = None
    _bounds = None # 0 = Xmin, 1 = Ymin, 2 = Xmax, 3 = Ymax
    _sides = None
    def __init__(self):
        self._coords = []
        self._sides = []
        self._bounds = {}
        
    def add(self, point):
        self._coords.append(point)
        
    def precalculate(self):
        self.calculateBounds()
        self.calculateSides()
        
    def calculateBounds(self):
        for p in self._coords:
            if 0 not in self._bounds or p.x < self._bounds[0]:
                self._bounds[0] = p.x
                
            if 1 not in self._bounds or p.y < self._bounds[1]:
                self._bounds[1] = p.y
                
            if 2 not in self._bounds or p.x > self._bounds[2]:
                self._bounds[2] = p.x
                
            if 3 not in self._bounds or p.y > self._bounds[3]:
                self._bounds[3] = p.y
    def calculateSides(self):
        self._sides = []
        i = 0
        for p in self._coords:
            if len(self._coords) - 1 == i:
                pn = self._coords[0]
                self._sides.append(Line(p,pn))
                break
            else:
                pn = self._coords[i+1]
                self._sides.append(Line(p,pn))
            i = i + 1
    def isPointInside(self, p):
        if(p.x < self._bounds[0] or p.x > self._bounds[2] or p.y < self._bounds[1] or p.y > self._bounds[3]):
            return False
        intersects = 0
        ray = Line(Point(self._bounds[0]-10, p.y), p)
        for side in self._sides:
            if self.areLinesIntersecting(ray, side):
                intersects = intersects + 1
        if intersects % 2 == 0:
            return False
        else:
            return True
    
    def isXYInside(self, x, y):
        return self.isPointInside(Point(x,y))
        
    def areLinesIntersecting(self, line1, line2):
        # Props to Toto aka Thomas aka Cheese-eating surrender monkey for the following formulas
        p = ((line1.p1.y - line1.p2.y) * (line2.p2.x - line2.p1.x)) + ((line1.p2.x - line1.p1.x) * (line2.p2.y - line2.p1.y))
        if(p == 0):
            return False
        else:
            m = ((line2.p2.x - line2.p1.x) * (line1.p1.x - line2.p1.x) + (line1.p2.x - line1.p1.x) * (line1.p1.y - line2.p1.y)) / p
            if(m >= 0 and m <= 1):
                return False
            else:
                toto = ((line2.p1.y - line2.p2.y) * (line1.p1.x - line2.p1.x) + (line1.p1.y - line1.p2.y) * (line1.p1.y - line2.p1.y)) / p
                if(toto >= 0 and toto <= 1):
                    return True
                else:
                    return False
        
        