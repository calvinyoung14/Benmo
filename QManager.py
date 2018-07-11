from PaxosManager import PaxosManager
import time
from threading import Thread, BoundedSemaphore
import copy, json




class QManager(object):


	def __init__(self, poll):
		self.queue = []
		self.pollName = poll


	def minusP(self):
		self.qSema.acquire()

	def plusV(self):
		self.qSema.relsease()

	def add(self, command):
		if(len(self.queue) >= 10):
			print("Queue is Full, Please Wait")
		else:
			self.queue.append(command)


	def queueTrigger(self, pMan):
			pMan.startPaxos(self.queue)

	def clearQueue(self, block):
		for payment in block:
			try:
				self.queue.remove(payment)
			except ValueError:
				pass


	def printQueue(self):
		print(self.queue)


	def saveQueue(self):
		with open('data/serverQueue'+str(self.pollName)+'.txt', 'w') as outfile:
		    json.dump(self.queue, outfile)

	def loadQueue(self):
		with open('data/serverQueue'+str(self.pollName)+'.txt', 'r') as infile:
			savedQueue = json.load(infile)
			self.queue = copy.deepcopy(savedQueue)
