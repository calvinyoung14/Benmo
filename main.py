import sys, threading, time
from threading import BoundedSemaphore, Thread 


def printList(xl):
	time.sleep(2)
	print(xl)

myList = []
myList.append(3)


th = Thread(target=printList, args=(myList,))
myList.append(3)
th.start()
myList.append(3)

