from Blockchain import Blockchain
from Paxos import Paxos
from socket import error as sock_err
from threading import BoundedSemaphore, Thread 
import copy, errno, json, socket, time, random, sys, logging



class PaxosManager():


    def __init__(self, pollName, que):

        UDP_IP = "127.0.0.1"
        UDP_PORT = 5000 + pollName                ###SHOULD BE READ FORM FIEL

        self.endFlag = False
        self.netArray = [True] * 6
        self.IPAddress = [0,0,0,0,0] 
        self.loadIP()

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #THIS CRAP SHOULD BE CLASS VAR
        self.serverSocket.bind(('', UDP_PORT))
        self.serverSocket.settimeout(10)

        self.theClock = None

        self.bchain = Blockchain(pollName)
        self.bchain.loadBlockchain()

        self.paxos = Paxos(pollName, self.serverSocket, self.bchain, self.netArray, self.IPAddress) #IFFFFFFFFFFFFFY
        self.paxos.loadPaxos()

        self.theQueue = que

    def loadIP(self):
        with open('data/IPconfig.txt', 'r') as infile:
            data = json.load(infile)
            logging.debug(data)
            self.IPAddress = copy.deepcopy(data)
    '''def saveIP(self):
        with open('data/IPconfig.txt', 'w') as outfile:
            json.dump(self.IPAddress, outfile)
    '''

    def startPaxos(self, value):
        self.paxos.randTemp = value
        self.paxos.propose(self.bchain.depth())


    def print_info(self):
        print(self.paxos.ballotNum)
        print(self.paxos.acceptNum)
        print(self.paxos.acceptVal)
        print(self.bchain.printChain())

    def printBchain(self):
        self.bchain.printChain()

    def printBalance(self):
        print("--===--")
        print("Current Balance:", self.bchain.pretendMoney)
        print("Money in Transfer:", self.bchain.realMoney - self.bchain.pretendMoney)
        print("--===--")

    def failNet(self, nnum):
        self.netArray[nnum] = False

    def fixNet(self, nnum):
        self.netArray[nnum] = True

    def serverThread(self):

        while True and not(self.endFlag):
            #print("---Waiting For Message---")
            try:
                data, addr = self.serverSocket.recvfrom(1024)
            except socket.timeout:
                continue

            msg_decode = data.decode('utf-8')
            load_msg = json.loads(msg_decode)

            if(load_msg[0] == "prep"):
                print("---Recieved Prep Ballot", load_msg[1])
                th = Thread(target=self.paxos.ackPropose, args=(addr, load_msg[1]))
                th.start()  

            elif(load_msg[0] == 'ackP' and not(self.paxos.acceptPhase)):
                print("---Recieved Prep Ack from Server", addr[1]-5000)
                if(self.paxos.ballotCompare(load_msg[1], self.paxos.ballotNum)): #depth???????????????????????????
                    self.paxos.ackPrepCounter+=1
                    self.paxos.acceptList.append(load_msg[-3:])
                    print("~~~AckPrep Counter:", self.paxos.ackPrepCounter)
                else:
                    print("~~~AckPrep from Server", addr[1]-5000, "ignored, low ballot.", load_msg[1])
                

                if(self.paxos.ackPrepCounter >= self.paxos.majority):
                    print("===Phase 2: Accept===")
                    self.paxos.acceptPhase = True
                    th=Thread(target=self.paxos.accept)
                    th.start()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~after the value~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                


            elif(load_msg[0] == 'acpt'):
                    
                    th = Thread(target=self.paxos.ackAccept, args=(addr, load_msg[1], load_msg[2]))
                    th.start()
                    #HELP?

            elif(load_msg[0] == 'ackA' and not(self.paxos.decidePhase)):
                print("---Recieved Accept Ack from Server", addr[1]-5000)
                if(self.paxos.ballotCompare(load_msg[1], self.paxos.ballotNum)):
                    self.paxos.ackAcptCounter+=1
                    print("~~~AckACCept Counter:", self.paxos.ackAcptCounter)
                else:
                    print("~~~AckAccept from Server", addr[1]-5000, "ignored, low ballot.", load_msg[1])
                
                
                if(self.paxos.ackAcptCounter >= self.paxos.majority):
                    print("===Phase 3: Decide===")
                    self.paxos.decidePhase = True
                    th = Thread(target=self.paxos.decide)
                    th.start()

            elif(load_msg[0] == 'decide'):
                print(">>>DECISION MADE<<<")
                self.paxos.reset()

                th = Thread(target = self.bchain.addBlock, args=(load_msg[2], self.theQueue, self.paxos))
                th.start()
                #1 acceptNum #2 accpetVal
              
                #self.paxos.reset()
            elif(load_msg[0] == "giffBlockchain"):
                print("---Recieved BC update request from Server", addr[1]-5000)
                self.paxos.sendBC(addr)

            elif(load_msg[0] == "updateBC"):
                print("---Recieved Blockchain from Server", addr[1]-5000)
                th = Thread(target = self.bchain.updateBC, args=(load_msg[1], self.theQueue, self.paxos))
                th.start()
            
            else:
                print("~~~Recv:", load_msg[0], "from Server", addr[1]-5000, "Not Processed")
            