import copy, json, threading, time, logging
from threading import BoundedSemaphore, Thread 


class Paxos():


    def __init__(self, pollName, socket, theBC, nArr, ipadd):
        self.pollName = pollName
        self.sendSocket = socket
        self.ourBlockChain = theBC
        self.ourNetArray = nArr
        self.IPAdress = ipadd

        self.majority = 2
        self.ackPrepCounter = 0
        self.ackAcptCounter = 0
        self.randTemp = 0

        self.ballotNum = [0,0,0] #Should be 0, pollname, 0?
        self.acceptNum = [0,0,0]
        self.acceptVal = None
        self.acceptList = []
        self.acceptPhase = False
        self.decidePhase = False

        self.keysema = BoundedSemaphore(1)

    def reset(self):                    #WE RESET WHEN SEND DECIDE, SHOULD RESET ACCNUM>?
        self.ackPrepCounter = 0
        self.ackAcptCounter = 0
        self.randTemp = 0

        self.ballotNum = [0, 0, 0]
        self.acceptNum = [0, 0, 0]
        self.acceptVal = None
        self.acceptList = []
        self.acceptPhase = False
        self.decidePhase = False


#ORDER: POLLNAME

    def savePaxos(self):
        with open('data/paxos'+str(self.pollName)+'.txt', 'w') as outfile:
            json.dump((self.ackPrepCounter, self.ackAcptCounter, self.randTemp, self.ballotNum, self.acceptNum, self.acceptVal, self.acceptList, self.acceptPhase, self.decidePhase), outfile)

    def loadPaxos(self):
        with open('data/paxos'+str(self.pollName)+'.txt' , 'r') as infile:
            data = json.load(infile)

            self.ackPrepCounter = data[0]
            self.ackAcptCounter = data[1]
            self.randTemp = data[2]

            self.ballotNum = data[3] #Should be 0, pollname, 0?
            self.acceptNum = data[4]
            self.acceptVal = data[5]
            self.acceptList = data[6]
            self.acceptPhase = data[7]
            self.decidePhase = data[8]



    def getNewBallot(self, depth):
        self.ballotNum[0]+=1
        self.ballotNum[1] = self.pollName
        self.ballotNum[2] = depth
        self.acceptPhase = False                            #temp fix
        self.decidePhase = False
        self.acceptList = []
        self.ackPrepCounter=0
        self.ackAcptCounter=0
        self.acceptVal = None
        #ballotNum[3] #has to be updated NO

    def sendBC(self, ipport):
        th1 = Thread(target = self.sendThread, args=("sendBC", ipport))
        th1.start()



    def propose(self, depth): #some value (queue/block)
        self.keysema.acquire()
        self.getNewBallot(depth)
        self.keysema.release()
        th1 = Thread(target=self.sendThread, args=("prepare", None))
        th1.start()
            #time.sleep(random.randint(10,15))

    def ballotCompare(self, bal1, bal2):
    #DEPTH HANDLE?
        if(bal1[0] > bal2[0] or (bal1[0] == bal2[0] and bal1[1] >= bal2[1])):
            return True
        else:
            return False;

    #PUT SELF ALWAYS 2nd!
    def depthCompare(self, bal1):
        if(bal1[2] > self.ourBlockChain.depth()):
            return "reqBC"
        elif(bal1[2] < self.ourBlockChain.depth()):
            return "sendBC"
        else:
            return "ok"
    


    def ackPropose(self, ipport, bal):
        self.keysema.acquire()

        if(self.depthCompare(bal) == "ok"):
            if(self.ballotCompare(bal, self.ballotNum)):
                #depth?
                self.ballotNum[0] = bal[0]
                self.ballotNum[1] = bal[1]
                th1 = Thread(target = self.sendThread, args=("ackPrep", ipport))
                th1.start()
            else:
                print("~~~Proposal is ignored from Server", ipport[1]-5000)
        elif(self.depthCompare(bal) == "reqBC"):
            print("~~~Detected: Blockchain is outdated! Req new BC!")
            th1 = Thread(target = self.sendThread, args=("reqBC", ipport))
            th1.start()

        elif(self.depthCompare(bal) == "sendBC"):
            print("~~~Detected: Other server has old Blockchain! Send BC!")
            self.sendBC(ipport)

        self.keysema.release()
    

    def accept(self): #some val
        logging.debug("REEE BETTER ", self.acceptList)
        self.keysema.acquire()

        self.acceptNum = copy.deepcopy(self.ballotNum)
        tempAccept = [-1,-1,-1] #IS DIS RIGHT?
        #send out myVal
        self.acceptVal = copy.deepcopy(self.randTemp)
        for elements in self.acceptList:
            #Each of elements is: ballnum-0 acceptnum-1 acceptval-2
            if(elements[2] != None):
                if(self.ballotCompare(elements[1], tempAccept)):
                    tempAccept = copy.deepcopy(elements[1])
                    self.acceptVal = copy.deepcopy(elements[2])
       
        if(tempAccept != [-1,-1,-1]):
            self.acceptNum = copy.deepcopy(tempAccept)

        th = Thread(target = self.sendThread, args=("accept", None))
        th.start()

        self.keysema.release()



    def ackAccept(self, ipport, bal, accV):
        self.keysema.acquire()

        if(self.depthCompare(bal) == "ok"):
            if(self.ballotCompare(bal, self.ballotNum)):
                self.acceptNum = copy.deepcopy(bal)
                self.acceptVal = copy.deepcopy(accV)
                print('---Processed Accept from Server', ipport[1]-5000)

                th = Thread(target = self.sendThread, args=("ackA", ipport))
                th.start()

            else:
                print("---Accept is ignored from: ", ipport[1]-5000, "ballot num low.")

        elif(self.depthCompare(bal) == "reqBC"):
            print("~~~Detected: Blockchain is outdated! Req new BC!")
            th1 = Thread(target = self.sendThread, args=("reqBC", ipport))
            th1.start()

        elif(self.depthCompare(bal) == "sendBC"):
            print("~~~Detected: Other server has old Blockchain! Send BC!")
            self.sendBC(ipport)

        self.keysema.release()



    def decide(self):
        th = Thread(target = self.sendThread, args=("decide", None))
        th.start()


    def sendThread(self, sendType, ackIPPort):

            if(sendType == "prepare"):
                print("+++Sending Prepare to All Server+++")
                dump_msg = json.dumps(('prep', self.ballotNum))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                for i in range(1, 6):
                    if(self.ourNetArray[i]):
                        self.sendSocket.sendto(MESSAGE, (self.IPAdress[i-1],5000+i)) #will have to be updated
                    else:
                        print("~~~Connection failed to Server ", i)

            elif(sendType == "ackPrep"):
                print("+++Sending ackPrep to", self.ballotNum, "to Server", ackIPPort[1]-5000)
                dump_msg = json.dumps(('ackP', self.ballotNum, self.acceptNum, self.acceptVal))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                if(self.ourNetArray[ackIPPort[1]-5000]):
                    self.sendSocket.sendto(MESSAGE, ackIPPort)
                else:
                    print("~~~Connection failed to Server ", ackIPPort[1]-5000)
           
            elif(sendType == "accept"):
                print("+++Sending Accept to All Servers+++")
                dump_msg = json.dumps(('acpt', self.ballotNum, self.acceptVal))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                for i in range(1, 6):
                    if(self.ourNetArray[i]):
                        self.sendSocket.sendto(MESSAGE, (self.IPAdress[i-1],5000+i)) #will have to be updated
                    else:
                        print("~~~Connection failed to Server ", i)

            elif(sendType == "ackA"):
                print("+++Sending ackAccept to Server", ackIPPort[1]-5000)
                dump_msg = json.dumps(('ackA', self.acceptNum, self.acceptVal))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                if(self.ourNetArray[ackIPPort[1]-5000]):
                    self.sendSocket.sendto(MESSAGE, ackIPPort)
                else:
                    print("~~~Connection failed to Server ", ackIPPort[1]-5000)

            elif(sendType == "decide"):
                print("+++Sending Decide to All Servers+++")
                dump_msg = json.dumps(('decide', self.acceptNum, self.acceptVal))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                for i in range(1, 6):
                    if(self.ourNetArray[i]):
                        self.sendSocket.sendto(MESSAGE, (self.IPAdress[i-1], 5000+i)) #will have to be updated
                    else:
                        print("~~~Connection failed to Server ", i)

            
            elif(sendType == "reqBC"):
                print("+++Requesting Blockchain from Server", ackIPPort[1]-5000)
                dump_msg = json.dumps(('giffBlockchain',))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                if(self.ourNetArray[ackIPPort[1]-5000]):
                    self.sendSocket.sendto(MESSAGE, ackIPPort)
                else:
                    print("~~~Connection failed to Server ", ackIPPort[1]-5000)

            elif(sendType == "sendBC"):
                print("+++Sending Blockchain from Server", ackIPPort[1]-5000)
                dump_msg = json.dumps(('updateBC', self.ourBlockChain.transactions))
                MESSAGE = bytes(dump_msg, "utf-8")
                time.sleep(1.5)
                if(self.ourNetArray[ackIPPort[1]-5000]):
                    self.sendSocket.sendto(MESSAGE, ackIPPort)
                else:
                    print("~~~Connection failed to Server ", ackIPPort[1]-5000)

            else:
                print("SEND THREAD BROKEBACK")
                
