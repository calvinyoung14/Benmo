import threading

def printit():
  threading.Timer(2.0, printit).start()
  print("Hello, World!")

printit()
