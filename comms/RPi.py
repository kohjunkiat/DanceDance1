import queue
import socket
import sys
import base64
import time
import threading
import os
#import arduino as my_Ard 
from Crypto import Random
from Crypto.Cipher import AES


#global variables
dataQueue = queue.Queue(1)
queueLock = threading.Lock()


def Main_Run():
    
    myThread1 = toMLtoServer()
 #   myThread2 = listen()
    input("Press ENTER when the server is ready....")
    myThread1.start()
  #  myThread2.start()

class toMLtoServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.my_pi = RaspberryPi(ip_addr, port_num)

    def run(self):
        print("inside RPi thread")
        danceMove = ""
        power = "12345"
        voltage = "12345"
        current = "12345"
        cumpower = "1234567"
        while True:
            #queueLock.acquire()
            if not dataQueue.empty(): #check if queue is empty or not. If empty, dont try to take from queue
                #packet_data = dataQueue.get()
                print("there is data inside the queue")
                #print("data from queue: " + str(packet_data)) #check for multithreading using this line
                #power = packet_data["power"]
                #voltage = packet_data["voltage"]
                #current = packet_data["current"]
                #cumpower = packet_data["cumpower"]
                #danceMove = my_ML.give(packet_data)
            #queueLock.release()
            danceMove = sys.stdin.readline().strip()
            if danceMove is not None : 
                data = Data(self.my_pi.sock)
                data.sendData(danceMove, power, voltage, current, cumpower)
                dataQueue.queue.clear()
            

class listen(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        my_Ard.init()
        print("connected to arduino")

    def run(self):
        print("inside Arduino thread")
        while True:
            packet = my_Ard.listen() #packet is in dict format
            #queueLock.acquire()
            #if not dataQueue.full(): #check if queue is full. If full, dont put it inside queue
                #print("data into queue: " + str(packet))
                #print("putting it inside queue")
                #dataQueue.put(packet)
            #queueLock.release()


class Data():
    def __init__(self, sock):
        self.sock = sock

    def sendData(self, move, power, voltage, current, cumpower):
        self.move = move
        self.current = current
        self.voltage = voltage
        self.power = power
        self.cumpower = cumpower
        dataToSend = ("#" + self.move + "|" + str(self.voltage) + "|" + str(self.current) + "|" + str(self.power) + "|" + str(self.cumpower) + "|")
        print("sending over data: " + dataToSend)
        paddedMsg = self.pad(dataToSend) #apply padding to pad message to multiple of 16
        encryptedData =self.encrypt(paddedMsg) #encrypt and encode in base64
#       print('encrypted + encoded data is : ' + str(encryptedData))
        self.sock.sendall(encryptedData)

    def pad(self,msg):
        extraChar = len(msg) % 16
        if extraChar > 0: #if msg size is under or over 16 char size
            padsize = 16 - extraChar
            paddedMsg = msg + (' ' * padsize)
        else:
            paddedMsg = msg
        return paddedMsg

    def encrypt(self, msg):
        secret_key = "1234512345123451" #dummy key for testing
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(secret_key,AES.MODE_CBC,iv)
        return base64.b64encode(iv + cipher.encrypt(msg)) #encrypted msg in octets(bytes) is transformed into sets of sextets. sextet value is used to determine the letter in Base64 table


class RaspberryPi():

    def __init__(self, server_add, server_port):
        self.server_add = server_add #address of the server (PC acting as server)
        self.server_port = int(server_port) #port of the server(PC acting as server)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #creates the socket object
        self.connect()

    def connect(self):
        server_fullAdd = (self.server_add, self.server_port)
        self.sock.connect(server_fullAdd) #connect to server socket
        print("connected to server websocket!")


if __name__ == '__main__':

    ip_addr = sys.argv[1]

    port_num = sys.argv[2]

    Main_Run()
