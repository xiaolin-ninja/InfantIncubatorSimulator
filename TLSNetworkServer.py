import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import infinc
import time
import math
import socket
import fcntl
import os
import errno
import random
import string
import ssl
from dotenv import load_dotenv

load_dotenv()

class SmartNetworkThermometer (threading.Thread):
    open_cmds = ["AUTH", "LOGOUT"]
    prot_cmds = ["SET_DEGF", "SET_DEGC", "SET_DEGK", "GET_TEMP", "UPDATE_TEMP"]

    def __init__ (self, source, updatePeriod, port) :
        threading.Thread.__init__(self, daemon = True) 
        #set daemon to be true, so it doesn't block program from exiting
        self.source = source
        self.updatePeriod = updatePeriod
        self.curTemperature = 0
        self.updateTemperature()
        self.tokens = []

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='./infinc.crt',keyfile='./private.key')

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", port))
        sock.listen()

        self.serverSocket = context.wrap_socket(sock, server_side=True)

        fcntl.fcntl(self.serverSocket, fcntl.F_SETFL, os.O_NONBLOCK)

        self.deg = "K"

    def setSource(self, source):
        self.source = source

    def setUpdatePeriod(self, updatePeriod):
        self.updatePeriod = updatePeriod 

    def setDegreeUnit(self, s):
        self.deg = s
        if self.deg not in ["F", "K", "C"] :
            self.deg = "K"

    def updateTemperature(self):
        self.curTemperature = self.source.getTemperature()

    def getTemperature(self):
        if self.deg == "C":
            return self.curTemperature - 273
        if self.deg == "F":
            return (self.curTemperature - 273) * 9 / 5 + 32
        return self.curTemperature

    def processCommands(self, token, cmds, conn):
        for c in cmds:
            if c == "LOGOUT":
                if token in self.tokens:
                    try:
                        self.tokens.remove(token)
                        conn.sendall(b"Logged Out\n")
                    except:
                        conn.sendall(b"Logout Failed\n")
            elif c == "SET_DEGF":
                self.deg = "F"
            elif c == "SET_DEGC":
                self.deg = "C"
            elif c == "SET_DEGK":
                self.deg = "K"
            elif c == "GET_TEMP":
                conn.sendall(b"%f\n" % self.getTemperature())
            elif c == "UPDATE_TEMP" :
                self.updateTemperature()
            elif c :
                conn.sendall(b"Invalid Command\n")

    def login(self, cs, conn): #process AUTH command
        if cs[0] == "AUTH":
            if cs[1] == os.environ.get('SECRET_KEY'):
                self.tokens.append(''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)))
                conn.sendall(self.tokens[-1].encode("utf-8"))
                print (self.tokens[-1])
            else:
                conn.sendall(b"Invalid Key\n")
        else : #unknown command
            conn.sendall(b"Invalid Command\n")


    def run(self) : #the running function
        while True : 
            try :
                conn, addr = self.serverSocket.accept()
                msg = conn.recv(1024).decode("utf-8").strip()

                if ' ' in msg: #expect an AUTH command
                    cmd = msg.split(' ')
                    if len(cmd) != 2: #if command is unexpected
                        conn.sendall(b"Bad Command\n")
                    else:
                        self.login(cmd, conn)
                elif ';' in msg: #expect AUTH_TOKEN;chain;commands
                    cmds = msg.split(';')

                    if len(self.tokens) == 0: #if no authentications
                        conn.sendall(b"Authenticate First\n")
                    elif cmds[0] in self.tokens: #if valid token
                        self.processCommands(cmds[0], cmds[1:], conn)
                    else:
                        conn.sendall(b"Bad Token\n")
                else:
                    conn.sendall(b"Bad Command\n")    
            except IOError as e :
                if e.errno == errno.EWOULDBLOCK :
                    #do nothing
                    pass
                else :
                    #do nothing for now
                    pass
                msg = ""
 

            self.updateTemperature()
            time.sleep(self.updatePeriod)


class SimpleClient :
    def __init__(self, therm1, therm2) :
        self.fig, self.ax = plt.subplots()
        now = time.time()
        self.lastTime = now
        self.times = [time.strftime("%H:%M:%S", time.localtime(now-i)) for i in range(30, 0, -1)]
        self.infTemps = [0]*30
        self.incTemps = [0]*30
        self.infLn, = plt.plot(range(30), self.infTemps, label="Infant Temperature")
        self.incLn, = plt.plot(range(30), self.incTemps, label="Incubator Temperature")
        plt.xticks(range(30), self.times, rotation=45)
        plt.ylim((20,50))
        plt.legend(handles=[self.infLn, self.incLn])
        self.infTherm = therm1
        self.incTherm = therm2

        self.ani = animation.FuncAnimation(self.fig, self.updateInfTemp, interval=500)
        self.ani2 = animation.FuncAnimation(self.fig, self.updateIncTemp, interval=500)

    def updateTime(self) :
        now = time.time()
        if math.floor(now) > math.floor(self.lastTime) :
            t = time.strftime("%H:%M:%S", time.localtime(now))
            self.times.append(t)
            #last 30 seconds of of data
            self.times = self.times[-30:]
            self.lastTime = now
            plt.xticks(range(30), self.times,rotation = 45)
            plt.title(time.strftime("%A, %Y-%m-%d", time.localtime(now)))


    def updateInfTemp(self, frame) :
        self.updateTime()
        t = self.convertTemperature(self.infTherm)
        self.infTemps.append(t)
        # self.infTemps.append(self.infTemps[-1] + 1)
        self.infTemps = self.infTemps[-30:]
        self.infLn.set_data(range(30), self.infTemps)
        return self.infLn,

    def updateIncTemp(self, frame) :
        self.updateTime()
        t = self.convertTemperature(self.incTherm)
        self.incTemps.append(t)
        #self.incTemps.append(self.incTemps[-1] + 1)
        self.incTemps = self.incTemps[-30:]
        self.incLn.set_data(range(30), self.incTemps)
        return self.incLn,

    def convertTemperature(self, therm):
        temp = therm.getTemperature()
        if therm.deg == "C" :
            return temp
        if therm.deg == "F" :
            return (temp - 32) * 5 / 9
        if therm.deg == "K" :
            return temp - 273


UPDATE_PERIOD = .05 #in seconds
SIMULATION_STEP = .1 #in seconds

#create a new instance of IncubatorSimulator
bob = infinc.Human(mass = 8, length = 1.68, temperature = 36 + 273)
#bobThermo = infinc.SmartThermometer(bob, UPDATE_PERIOD)
bobThermo = SmartNetworkThermometer(bob, UPDATE_PERIOD, 23456)
bobThermo.start() #start the thread

inc = infinc.Incubator(width = 1, depth=1, height = 1, temperature = 37 + 273, roomTemperature = 20 + 273)
#incThermo = infinc.SmartNetworkThermometer(inc, UPDATE_PERIOD)
incThermo = SmartNetworkThermometer(inc, UPDATE_PERIOD, 23457)
incThermo.start() #start the thread

incHeater = infinc.SmartHeater(powerOutput = 1500, setTemperature = 45 + 273, thermometer = incThermo, updatePeriod = UPDATE_PERIOD)
inc.setHeater(incHeater)
incHeater.start() #start the thread

sim = infinc.Simulator(infant = bob, incubator = inc, roomTemp = 20 + 273, timeStep = SIMULATION_STEP, sleepTime = SIMULATION_STEP / 10)

sim.start()

sc = SimpleClient(bobThermo, incThermo)

plt.grid()
plt.show()
