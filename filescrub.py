for i in range(1,6):

	with open("data/serverQueue"+str(i)+".txt", "w") as text_file:
	    text_file.write("[]")

	with open("data/blockchain"+str(i)+".txt", "w") as text_file:
	    text_file.write("[100, 100, []]")

	with open("data/paxos"+str(i)+".txt", "w") as text_file:
	    text_file.write("[0, 0, 0, [0, 0, 0], [0, 0, 0], null, [], false, false]")


