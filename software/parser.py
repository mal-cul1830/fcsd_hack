from Constants import *


class Parser():
    def __init__(self, filepath):
        self.commands = None
        self.vmFile = open(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.vmFile.close()

    def IdentifyType(self):
        command = self.commands[0]
        if command == 'push':
            return C_PUSH
         elif command == 'return':
            return C_RETURN
        elif command == 'label':
            return C_LABEL
        elif command == 'goto':
            return C_GOTO
        elif command == 'if-goto':
            return C_IF
        elif command == 'pop':
            return C_POP
        elif command == 'function':
            return C_FUNCTION
        elif command == 'call':
            return C_CALL
        elif command in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
            return C_ARITHMETIC
    def getCommand(self):
        while True:
            line = self.vmFile.readline()
            if not line:
                self.commands = None
                return self.commands
            else:
                line = line.rstrip().lstrip()

                c = line.find('//') #finding where the comment starts 
                if c != -1:
                    line = line[:c] #filtering out the part where the comment starts

                if line != '':
                    self.commands = line.split()
                    return self.commands

    def arg1(self):
        if self.IdentifyType() == C_ARITHMETIC:
            return self.commands[0]
        else:
            return self.commands[1]

    def arg2(self):
        if self.IdentifyType() in [C_PUSH, C_POP, C_FUNCTION, C_CALL]:
            return self.commands[2]