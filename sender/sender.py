import socket
import sys
import os
import time
import datetime
import requests
import threading

pivotTime = 0

def printUsage():
	print ("usage : python sender.py [working directory] [fuzzer name] [fuzzing_os] [fuzzing program] [receiver server IP] [option]")
	print ("""
Option

-a [alias]
	set alias option.
	This is an option that set this crash sender's alias.
	If you do not specify this option, alias will be set default value, None

-p [port]
	set ping port option.
	This is an option that set crash sender's ping check port.
	If you do not specify this option, ping port will be set default value, 1337
		""")

def pingReceiver(pingPort):
	HOST = ''                   # Symbolic name meaning all available interfaces
	PORT = int(pingPort)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((HOST, PORT))
	while 1:
		s.listen(1)
		conn, addr = s.accept()
		print ('Connected by', addr)
		while 1:
			data = conn.recv(1024)
			if not data: break
			conn.sendall(b'success')
		conn.close()

def sendVmToReveiver(fuzzer, fuzzingProgram, fuzzing_os, receiverIP, alias, pingPort):
	payload = {'fuzzer' : fuzzer, 'fuzzingProgram' : fuzzingProgram, 'fuzzing_os' : fuzzing_os, 'alias' : alias, 'pingPort' : pingPort}
	r = requests.post(receiverIP+"/vm", data=payload)

def sendCrashToReceiverWin(crashName, fuzzingProgram, receiverIP, exploitable):
	payload = {'crashName' : crashName, 'fuzzingProgram' : fuzzingProgram, 'exploitable' : exploitable}
	r = requests.post(receiverIP+"/crash", data=payload)

def searchDirWin(workDir, fuzzingProgram, receiverIP):
	newPivotTime = pivotTime
	rootDir = os.listdir(workDir)
	for exploitableDir in rootDir:									#get files
		workExploitableDir = os.path.join(workDir, exploitableDir)
		exploitableDirCreateTime = datetime.datetime.fromtimestamp(os.path.getmtime(workExploitableDir))		#get file created time
		if(exploitableDirCreateTime > pivotTime):
			crashDir = os.listdir(workExploitableDir)
			for crashDirName in crashDir:
				crashDirCreateTime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(workExploitableDir, crashDirName)))		#get file created time
				if(crashDirCreateTime > pivotTime):
					sendCrashToReceiverWin(crashDirName, fuzzingProgram, receiverIP, exploitableDir)
					print ("crash send success!")
					newPivotTime = max(newPivotTime, crashDirCreateTime)
	return newPivotTime

def sendCrashToReceiver(crashName, fuzzingProgram, receiverIP):
	payload = {'crashName' : crashName, 'fuzzingProgram' : fuzzingProgram, 'exploitable' : 'this fuzzer not support'}
	r = requests.post(receiverIP+"/crash", data=payload)

def searchDir(workDir, fuzzingProgram, receiverIP):
	newPivotTime = pivotTime
	filenames = os.listdir(workDir)
	for crashName in filenames:									#get files
		full_crashName = os.path.join(workDir, crashName)		#get file name
		crashCreateTime = datetime.datetime.fromtimestamp(os.path.getctime(full_crashName))		#get file created time
		if(crashCreateTime > pivotTime):
			sendCrashToReceiver(crashName, fuzzingProgram, receiverIP)
			print ("crash send success!")
			newPivotTime = max(newPivotTime, crashCreateTime)
	return newPivotTime


if __name__ == "__main__":
	argc = len(sys.argv)
	alias = "None"
	pingPort = "None"

	for i in range(0, argc):
		if sys.argv[i][0] == '-':
			if sys.argv[i][1] == 'h':		#help option
				printUsage()
				exit(1)
			if sys.argv[i][1] == 'a':		#set alias option
				if i+1 >= argc:
					print ("error : specify the alias!")
					exit(1)
				alias = sys.argv[i+1]
			if sys.argv[i][1] == 'p':		#set port option
				if i+1 >= argc:
					print ("error : specify the port!")
					exit(1)
				pingPort = sys.argv[i+1]

	if argc < 4:
		printUsage()
		exit(1)

	workDir = sys.argv[1]
	fuzzer = sys.argv[2]
	fuzzing_os = sys.argv[3]
	fuzzingProgram = sys.argv[4]
	receiverIP = sys.argv[5]
		

	pivotTime = datetime.datetime.now()
	print ("search start time : [%s]" % str(pivotTime))

	if pingPort != "None":
		pingThread = threading.Thread(target=pingReceiver, args=(pingPort,))
		pingThread.daemon = True
		pingThread.start()

	sendVmToReveiver(fuzzer, fuzzingProgram, fuzzing_os, receiverIP, alias, pingPort)
	print ("vm reg success")

	while True:
		time.sleep(1)
		if fuzzing_os == 'W':
			pivotTime = searchDirWin(workDir, fuzzingProgram, receiverIP)
		else:
			pivotTime = searchDir(workDir, fuzzingProgram, receiverIP)
