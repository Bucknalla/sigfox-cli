import sys, os, re, json, getpass
import glob
import serial
from clint.arguments import Args
from clint.textui import prompt, puts, colored, validators, indent

commandList = {}
portSelection = None

def getCommands(library):
    cur_dir = os.path.dirname(__file__) # Absolute Directory
    rel_path = "Config/AT_Libraries/" + library
    abs_file_path = os.path.join(cur_dir, rel_path)
    jsonFile = open(abs_file_path, "r")
    f = json.load(jsonFile)
    jsonFile.close()
    for key, value in f["Commands"].items():
        commandList.update({key : value})
    return commandList

def getConfig():
    jsonFile = open("Config/config.json", "r")
    data = json.load(jsonFile)
    jsonFile.close()
    baudRate = data['BaudRate']
    AT_Library = data['AT_Library']
    return(baudRate, AT_Library)

def serialPorts():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
	if not result:
		print "No devices found..."
		sys.exit()
    return result

# Options for using Sigfox Modules

class Sigfox:
	
    def __init__(self, name, baud, library):
        self.name = name
        self.baud = baud
        self.library = library
        self.commands = getCommands(library)

    def handleCommand(self, command):
        if command == 1:
            self.__getDeviceId()
        elif command == 2:
            self.__getPAC()
        elif command == 3:
            self.__getLibraryVer()
        elif command == 4:
            self.__sendMessage()
        elif command == 5:
            self.__customCommand()
        elif command == 6:
            self.__config()
        else:
            return 'Error'
        raw_input("Press Enter to continue...")
        return setupBoard(False)

    # Retrieves Device ID
    def __getDeviceId(self):
        command = self.commands['ID'].encode('ascii', 'ignore')
        try:
        	with serial.Serial(self.name, self.baud, timeout=5) as ser:
        		ser.write(command+'\r')
        		line = ser.readline()
        		print line
        except serial.SerialException as e:
            print 'Could not connect to device...'

    # Retrieves Device PAC Number
    def __getPAC(self):
        command = self.commands['PAC'].encode('ascii', 'ignore')
        try:
        	with serial.Serial(self.name, self.baud, timeout=5) as ser:
        		ser.write(command+'\r')
        		line = ser.readline()
        		print line
        except serial.SerialException as e:
            print 'Could not connect to device...'

    # Retrieves Sigfox Library Version
    def __getLibraryVer(self):
        command = self.commands['Version'].encode('ascii', 'ignore')
        try:
        	with serial.Serial(self.name, self.baud, timeout=5) as ser:
        		ser.write(command+'\r')
        		line = ser.readline()
        		print line
        except serial.SerialException as e:
            print 'Could not connect to device...'

    # Sends a 12 Byte Sigfox Message, encoded in Hexidecimal
    def __sendMessage(self):
        sigfoxPattern = re.compile("^[0-9A-F]{1,24}$")
        command = self.commands['Send'].encode('ascii', 'ignore')
        payload = prompt.query("Message (Hexidecimal):", validators=[validators.RegexValidator(sigfoxPattern, 'Invalid Payload')])
        try:
            with serial.Serial(self.name, self.baud, timeout=10) as ser:
        		ser.write(command+payload+'\r')
        		line = ser.readline()
        		print line
        except serial.SerialException as e:
            print 'Could not connect to device...'

    # Allows user to enter a custom command
    def __customCommand(self):
        command = prompt.query("Custom:")
        try:
            with serial.Serial(self.name, self.baud, timeout=10) as ser:
                ser.write(command+'\r')
                line = ser.readline()
                print line
        except serial.SerialException as e:
            print 'Could not connect to device...'

    # Initalises the Configuration Settings
    def __config(self):
        global portSelection
        configList = [{'selector':'1','prompt':'Set Baud Rate'},
                        {'selector':'2','prompt':'Set Login Details'},
                        {'selector':'3','prompt':'Set AT Library'},
                        {'selector':'4','prompt':'Change Device'},
                        {'selector':'5','prompt':'About'},
                        {'selector':'0','prompt':'Back'}]

        config = int(prompt.options("Config:", configList))

        if config == 1:
            baudRate = prompt.query("Baud rate:", validators=[validators.IntegerValidator()])
            self.__modifyConfigFiles('BaudRate', baudRate)
        elif config == 2:
            print 'Under Construction...'
            os.environ["SIGFOX_USR"] = prompt.query("Username:")
            os.environ["SIGFOX_PWD"] = getpass.getpass('Password:')
        elif config == 3:
            libraryOptions = self.__getLibraries()
            libraryChoice = int(prompt.options("Current Library: " + self.library + "\n" + "Select:", libraryOptions))
            library = libraryOptions[libraryChoice-1]
            getCommands(library)
        elif config == 4:
            boards = serialPorts()
            boardOption = prompt.options("Select Device:", boards)
            portSelection = boards[boardOption-1]
        elif config == 5:
            self.displayAbout()
        elif config == 0:
            setupBoard(False)
        else:
            return 'Error'
        raw_input("Press Enter to continue...")
        self.__config()

    def __modifyConfigFiles(self, index, data):
        jsonFile = open("Config/config.json", "r")
        f = json.load(jsonFile)
        jsonFile.close()

        f[index] = data

        jsonFile = open("Config/config.json", "w+")
        jsonFile.write(json.dumps(f))
        jsonFile.close()

    def __getLibraries(self):
        cur_dir = os.path.dirname(__file__)
        rel_path = "Config/AT_Libraries/"
        abs_file_path = os.path.join(cur_dir, rel_path)
        options = os.listdir(abs_file_path)
        return options

    def displayAbout(self):
        with open("Config/about.txt", "r") as myfile:
            artwork=myfile.read()
        artwork.split('\n')
        puts(colored.magenta(artwork))



# Initalise Command Prompt
def setupBoard(inital=True):
    global portSelection
    if inital==True:
        boards = serialPorts()
        boardOption = prompt.options("Select Device:", boards)
        portSelection = boards[boardOption-1]
    baudRate, library = getConfig()

    commandList = [{'selector':'1','prompt':'Get ID'},
                    {'selector':'2','prompt':'Get PAC'},
                    {'selector':'3','prompt':'Get Library Version'},
                    {'selector':'4','prompt':'Send Message'},
                    {'selector':'5','prompt':'Custom Command'},
                    {'selector':'6','prompt':'Config'},
                    {'selector':'0','prompt':'Exit'}]

    command = int(prompt.options("Command:", commandList))

    if command == 0:
        print "Exiting program..."
        sys.exit(0)

    if command != 6:
        puts(colored.blue('Initialising {0}'.format(portSelection)))

    device = Sigfox(portSelection, baudRate, library)
    device.handleCommand(command)

if __name__ == '__main__':
    setupBoard()
