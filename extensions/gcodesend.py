#!/usr/bin/env python 
#inspired by https://github.com/bborncr/gcodesender.py

import inkex, cubicsuperpath, simplepath, cspsubdiv, os.path, serial, time, sys, string, gettext, datetime


#copied from grbl_serial.py
def findPort():
	# Find a GRBL board connected to a USB port.
	try:
		from serial.tools.list_ports import comports
	except ImportError:
		comports = None
		return None
	if comports:
		comPortsList = list(comports())
		for port in comPortsList:
			desc = port[1].lower()
			isUsbSerial = "usb" in desc and "serial" in desc
			isArduino = "arduino" in desc 
			isCDC = "CDC" in desc 
			if isUsbSerial or isArduino or isCDC:
				return port[0]
				
	return None

def testPort(comPort):
	'''
	Return a SerialPort object for the first port with a GRBL board.
	YOU are responsible for closing this serial port!
	'''
	if comPort is not None:
		try:
			serialPort = serial.Serial()
			serialPort.baudrate = 9600
			serialPort.timeout = 1.0
			serialPort.rts = False
			serialPort.dtr = True
			serialPort.port = comPort
			serialPort.open()
			time.sleep(2)
			while True:
				strVersion = serialPort.readline()
				if len(strVersion) == 0:
					break
				if strVersion and strVersion.startswith('Grbl'):
					return serialPort
			serialPort.close()
		except serial.SerialException:
			pass
		return None
	else:
		return None

# Return a GrblSerial object
def openPort(self):
	foundPort = findPort()
	serialPort = testPort(foundPort)
	if serialPort:
		g = GrblSerial(serialPort, 1)
		# Set absolute mode
		 
			
		if self.options.setupType == "align-mode":
			g.command('G90\r')
			f = open("costycnc.nc", 'r')

		elif self.options.setupType == "toggle-pen":
			g.command('G91\r')
			f = open("home.nc", 'r')
		line = f.readline()
		while line:
			g.command(line)
			inkex.debug(line)
			line = f.readline()
		f.close()
		return g
	return None

def escaped(s):
	r = ''
	for c in s:
		if ord(c) < 32:
			r = r + ('<%02X>' % ord(c))
		else:
			r = r + c
	return r

class GrblSerial(object):
	def __init__(self, port, doLog):
		self.port = port
		self.doLog = doLog

	def log(self, type, text):
		ts = datetime.datetime.now()
		try:
			with open("costycnc-serial.log", "a") as myfile:
				myfile.write('--- %s\n%s\n%s\n' % (ts.isoformat(), type, escaped(text)))
		except:
			inkex.errormsg(gettext.gettext("Error logging serial data."))

	def close(self):
		if self.port is not None:
			try:
				self.port.close()
			except serial.SerialException:
				pass

	def write(self, data):
		if self.doLog:
			self.log('SEND', data)
		self.port.write(data)

	def readline(self):
		data = self.port.readline()
		inkex.debug(data)
		if self.doLog:
			self.log('RECV', data)
		return data
	
	def query(self, cmd):
		if (self.port is not None) and (cmd is not None):
			response = ''
			try:
				self.write(cmd)
				response = self.readline()
				nRetryCount = 0
				while (len(response) == 0) and (nRetryCount < 100):
					if self.doLog:
						self.log('QUERY', 'read %d' % nRetryCount)
					response = self.readline()
					nRetryCount += 1
					if self.doLog:
						self.log('QUERY', 'response is '+response)
				# swallow 'ok'
				nRetryCount = 0
				ok = self.readline()
				while (len(ok) == 0) and (nRetryCount < 100):
					ok = self.readline()
					nRetryCount += 1
			except serial.SerialException:
				inkex.errormsg(gettext.gettext("Error reading serial data."))
			return response
		else:
			return None

	def command(self, cmd):
		if (self.port is not None) and (cmd is not None):
			try:
				self.write(cmd)
				response = self.readline()
				nRetryCount = 0
				while (len(response) == 0) and (nRetryCount < 30):
					# get new response to replace null response if necessary
					response = self.readline()
					nRetryCount += 1
				if 'ok' in response.strip():
					return
				else:
					if (response != ''):
						inkex.errormsg('Error: Unexpected response from GRBL.') 
						inkex.errormsg('   Command: ' + cmd.strip())
						inkex.errormsg('   Response: ' + str(response.strip()))
					else:
						inkex.errormsg('GRBL Serial Timeout after command: %s)' % cmd.strip())
						sys.exit()
			except:
				inkex.errormsg('Failed after command: ' + cmd)
				sys.exit()

#finished copy from grbl_serial.py


class MyEffect(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("-f", "--flatness",
						action="store", type="float", 
						dest="flat", default=0.1,
						help="Minimum flatness of the subdivided curves")
	  
		self.OptionParser.add_option("--setupType",
			action="store", type="string",
			dest="setupType", default="align-mode",
			help="The setup option selected")                        
	def effect(self): 
	
		
		# Wake up 
		openPort(self)
		#grbl_serial.costy()
		
		


if __name__ == '__main__':
	e = MyEffect()
	e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 fileencoding=utf-8 textwidth=99
