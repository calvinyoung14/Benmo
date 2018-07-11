import socket
import errno
from socket import error as sock_err
import random
import sys
import time
import threading
from PaxosManager import PaxosManager
from QManager import QManager
from threading import Thread, BoundedSemaphore
import json
import copy
import logging

pollName = int(sys.argv[1])


#with open('init.txt') as f:
 #   lines = f.readlines()

#lines = [x.strip() for x in lines]

#TCP_IP = lines[0]

#if(pollName == '1'):
#elif(pollName == '2'):
#elif(pollName == '3'):


def statusChecker(qM, pM):
    while True and not(pM.endFlag):
        time.sleep(10)
        if (len(qM.queue) > 0):
            time.sleep(random.randint(1,2))
            print(">>>Queue Proccesed<<<")
            qM.queueTrigger(pM)
        

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False





pollName = int(sys.argv[1])
if(sys.argv[2] == 'd'):
    logging.basicConfig(level=logging.DEBUG)

logging.debug('DEBUG MODE ON')



qMan = QManager(pollName)
qMan.loadQueue()

pMan = PaxosManager(pollName, qMan)
#pMan.saveIP()
th1 = Thread(target=pMan.serverThread)
th1.start()
logging.debug(pMan.netArray)


th0 = Thread(target=statusChecker, args=(qMan, pMan))
th0.start()



while True and not(pMan.endFlag):
    command = input("Action to Take: ")
    data = command.split(" ")
    logging.debug(data)
    #break

    if (data[0] ==  "pay"):
        if(len(data) != 4):
            print("Error Format: pay <amt> <from> <to>")
        else:
            if(isInt(data[1]) and isInt(data[2]) and isInt(data[3])):
                amount = int(data[1])
                payer = int(data[2])
                reciever = int(data[3])

                if(payer != pollName or reciever < 1 or reciever > 5):
                    print("Wrong Server Numbers.")
                else:
                    if(pMan.bchain.pretendMoney - amount < 0):
                        print("Not Enough Funds.")
                    else:
                        if(payer != reciever):
                            pMan.bchain.pretendMoney -= amount
                            qMan.add([data[0], amount, payer, reciever])
                        else:
                            print('Can\'t pay youself.')
            else:
                print("Please type numbers.")

    elif(data[0] == "printBC"):
        pMan.printBchain()
    elif(data[0] == "printB"):
        pMan.printBalance()
    elif(data[0] == "printQ"):
        qMan.printQueue()
    elif(data[0] == "info"):
        pMan.print_info()
    elif(data[0] == "failNet" and len(data) == 2 and isInt(data[1]) and int(data[1]) > 0 and int(data[1]) <= 5):
        pMan.failNet(int(data[1]))
    elif(data[0] == "fixNet" and len(data) == 2 and isInt(data[1]) and int(data[1]) > 0 and int(data[1]) <= 5):
        pMan.fixNet(int(data[1]))
    elif (data[0] == "exit"):       
        print("EXITING...")
        qMan.saveQueue()
        pMan.bchain.saveBlockchain()
        pMan.paxos.savePaxos()
        pMan.endFlag = True
        print(threading.enumerate())
        sys.exit(0)

    else:
        print("Not a valid command")
