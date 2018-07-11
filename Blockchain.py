from threading import BoundedSemaphore, Thread
import json, logging

class Blockchain():

	def __init__(self, poll):
		self.pretendMoney = 100
		self.realMoney = 100
		self.transactions = []
		self.pollName = poll
		self.bcUpdateSema = BoundedSemaphore(1)
		self.bcAddSema = BoundedSemaphore(1)


	def updateMoney(self, block):
		for payment in block:
			if(payment[2] == self.pollName): 
				self.realMoney -= payment[1]
			elif(payment[3] == self.pollName):
				self.realMoney += payment[1]

		self.pretendMoney = self.realMoney

	def addBlock(self, block, que, paxos):
		self.bcAddSema.acquire()
		print(block)
		self.transactions.append(block)
		paxos.ballotNum[2] = self.depth()
		que.clearQueue(block)
		self.updateMoney(block)
		self.bcAddSema.release()



	def printChain(self):
		print("Depth: ", self.depth())
		for i in range(0, self.depth()):
			for payment in self.transactions[i]:
				print(payment[2], " paid ", payment[1], " to ", payment[3])
			print("\t|")
			print("\t|")
			print("\tV")
	
	def depth(self):
		return len(self.transactions)

	def updateBC(self, newtransactions, que, paxos):
		self.bcUpdateSema.acquire()

		if(len(newtransactions) > self.depth()):
			print("Updating own Blockchain")
			self.transactions = []
			for block in newtransactions:
				self.addBlock(block, que, paxos)

		self.bcUpdateSema.release()



		

	#ORDER: REAL$ PRETEND$ TRANSACTIONS POLLNAME


	def saveBlockchain(self):
		with open('data/blockchain'+str(self.pollName)+'.txt', 'w') as outfile:
		    json.dump((self.realMoney, self.pretendMoney, self.transactions), outfile)

	def loadBlockchain(self):
		with open('data/blockchain'+str(self.pollName)+'.txt', 'r') as infile:
			data = json.load(infile)
			self.realMoney = data[0]
			self.pretendMoney = data[1]
			self.transactions = data[2]