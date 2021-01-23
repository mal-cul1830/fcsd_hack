import glob
import argparse
import os.path

#user defined
from Constants import *

class CodeWriter():
    def CodeLine(self, line):
        self.f.write(line + '\n')

    def CodeLines(self, code):
        self.CodeLine('\n'.join(code))

    def __init__(self, filepath):
        self.f = open(filepath, 'w')
        self.label_num = 0
        self.return_label_num = 0
        self.if_label_num = 0
        self.writeInit()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        print(exception_type, exception_value)
        self.f.close()

    def Arithmetic(self, command):
        if command in ["add", "sub", "and", "or"]:
            self.BinaryOp(command)
        elif command in ["neg", "not"]:
            self.Unary(command)
        elif command in ["eq", "gt", "lt"]:
            self.Comp(command)

    def StackAccess(self, command, segment, index):

        i = int(index)

        if command == C_PUSH:
            if segment == "constant":
                self.CodeLines(['@%d' % i,'D=A'])
                self.PushD()
            elif segment in ["local", "argument", "this", "that"]:
                self.PushVS(segment, i)
            elif segment in ["temp", "pointer"]:
                self.PushStatic(segment, i)
            if segment == "static":
                self.CodeLines(["@%s.%d" % (self.FileNameNew, i),])
                self.CodeLine('D=M')
                self.PushD()

        elif command == C_POP:
            if segment in ["local", "argument", "this", "that"]:
                self.PopVS(segment, i)
            elif segment in ["temp", "pointer"]:
                self.PopStatic(segment, i)
            if segment == "static":
                self.PopM()
                self.CodeLines([
                    'D=M',
                    '@%s.%d' % (self.FileNameNew, i),
])
                self.CodeLine('M=D')

    def set_FileNameNew(self, file_name):
        self.FileNameNew = file_name

    def BinaryOp(self, command):
        self.PopM()
        self.CodeLine('D=M')
        self.PopM()
        if command == 'add':
            self.CodeLine('D=D+M')
        elif command == 'sub':
            self.CodeLine('D=M-D')
        elif command == 'and':
            self.CodeLine('D=D&M')
        elif command == 'or':
            self.CodeLine('D=D|M')
        self.PushD()

    def Unary(self, command):
        self.CodeLines([
            '@SP',
            'A=M-1',
        ])
        if command == 'neg':
            self.CodeLine('M=-M')
        elif command == 'not':
            self.CodeLine('M=!M')

    def Comp(self, command):
        self.PopM()
        self.CodeLine('D=M')
        self.PopM()
        l1 = self.NewLabel()
        l2 = self.NewLabel()
        if command == "eq":
            comp_type = "JEQ"
        elif command == "gt":
            comp_type = "JGT"
        elif command == "lt":
            comp_type = "JLT"
        self.CodeLines([
            'D=M-D',
            "@%s" % l1,
            'D;%s' % comp_type,
            'D=0',
            "@%s" % l2,
            '0;JMP',
            "(%s)" % l1,
            'D=-1',
            "(%s)" % l2,
        ])
        self.PushD()

    def PushVS(self, segment, index):
        if segment == "local":
            regName = "LCL"
        elif segment == "argument":
            regName = "ARG"
        elif segment == "this":
            regName = "THIS"
        elif segment == "that":
            regName = "THAT"
        self.CodeLines([
            '@'+str(regName),
            'A=M'
        ])
        for i in range(index):
            self.CodeLine('A=A+1')
        self.CodeLine('D=M')
        self.PushD()

    def PopVS(self, segment, index):
        if segment == "local":
            regName = "LCL"
        elif segment == "argument":
            regName = "ARG"
        elif segment == "this":
            regName = "THIS"
        elif segment == "that":
            regName = "THAT"
        self.PopM()
        self.CodeLines([
            'D=M',
            '@%s' % regName,
            'A=M'
        ])
        for i in range(index):
            self.CodeLine('A=A+1')
        self.CodeLine('M=D')

    def PushStatic(self, segment, index):
        if segment == "temp":
            baseLocation = TEMP_BASE_ADDRESS
        elif segment == "pointer":
            baseLocation = POINTER_BASE_ADDRESS
        self.CodeLines(["@"+str(baseLocation),])
        for i in range(index):
            self.CodeLine('A=A+1')
        self.CodeLine('D=M')
        self.PushD()

    def PopStatic(self, segment, index):
        if segment == "temp":
            baseLocation = TEMP_BASE_ADDRESS
        elif segment == "pointer":
            baseLocation = POINTER_BASE_ADDRESS
        self.PopM()
        self.CodeLines([
            'D=M',
            '@'+str(baseLocation),
        ])
        for i in range(index):
            self.CodeLine('A=A+1')
        self.CodeLine('M=D')

    def PushD(self):
        self.CodeLines([
            '@SP',
            'A=M',
            'M=D',
            '@SP',
            'M=M+1'])

    def NewLabel(self):
        self.label_num += 1
        return 'LABEL' + str(self.label_num)
    def PopM(self):
        self.CodeLines([
            '@SP',
            'M=M-1',
            'A=M'
        ])

    def IfLabel(self):
        self.if_label_num += 1
        return '_IF_LABEL_' + str(self.if_label_num)

    def ReturnLabel(self):
        self.return_label_num += 1
        return '_RETURN_LABEL_' + str(self.return_label_num)

    def writeNamedLabel(self, label):
        self.CodeLine("(%s)" % self.getLabel(label))

    def getLabel(self, label):
        try:
            return "%s$%s" % (self.curFName, label)
        except AttributeError:
            return "%s$%s" % ("null", label)

    def writeInit(self):
        self.writeSetSP(256)
        self.writeCall("Sys.init", 0)

    def writeSetSP(self, address):
        self.CodeLines([
            '@%d' % address,
            'D=A',
            '@SP',
            'M=D'
        ])

    def writeGoTo(self, label):
        self.CodeLines([
            '@%s' % self.getLabel(label),
            '0;JMP'
        ])

    def writeIf(self, label):
        self.write_pop_to_m_register()
        self.CodeLines([
            'D=M',
            '@%s' % self.getLabel(label),
            'D;JNE'
        ])

    def writeCall(self, FName, num_of_args):
        return_label = self.ReturnLabel()
        self.CodeLines([
            '// return-label',
            '@'+str(return_label),
            'D=A'
        ])
        self.PushD()  #push return-address
        self.CodeLines([
            '@LCL',
            'D=M',
        ])
        self.PushD()
        self.CodeLines([
            '@ARG',
            'D=M',
        ])
        self.PushD()
        self.CodeLines([
            '@THIS',
            'D=M',
        ])
        self.PushD()
        self.CodeLines([
            '@THAT',
            'D=M',
        ])
        self.PushD()

        self.CodeLines([
            '@SP',
            'D=M',
            '@5',
            'D=D-A',
            '@%d' % int(num_of_args),
            'D=D-A',
            '@ARG',
            'M=D',  # ARG = SP - n - 5
            '@SP',
            'D=M',
            '@LCL',
            'M=D'  # LCL = SP
        ])

        self.CodeLines([
            '@'+str(FName),
            '0;JMP',  # goto function
            '(%s)' % return_label
        ])

    def write_return(self):
        self.CodeLines([
            '@LCL',
            'D=M',
            '@R13',
            'M=D',  # R13 = FRAME = LCL
            '@5',
            'D=A',
            '@R13',
            'A=M-D',
            'D=M',  # D = *(FRAME-5) = return-address
            '@R14',
            'M=D',  # R14 = return-address
        ])
        self.write_pop_to_m_register()
        self.CodeLines([
            'D=M',
            '@ARG',
            'A=M',  # M = *ARG
            'M=D',  # *ARG = pop()

            '@ARG',
            'D=M+1',
            '@SP',
            'M=D',  # SP = ARG + 1

            '@R13',
            'AM=M-1',  # A = FRAME-1, R13 = FRAME-1
            'D=M',
            '@THAT',
            'M=D',  # THAT = *(FRAME-1)

            '@R13',
            'AM=M-1',


            'D=M',
            '@THIS',
            'M=D',  # THIS = *(FRAME-2)

            '@R13',
            'AM=M-1',
            'D=M',
            '@ARG',
            'M=D',  # ARG = *(FRAME-3)

            '@R13',
            'AM=M-1',
            'D=M',
            '@LCL',
            'M=D',
            '@R14',
            'A=M',
            '0;JMP'
        ])

    def writeFunct(self, FName, nlocal):
        self.CodeLines([
            '(%s)' % FName,
            'D=0'
        ])
        for i in range(int(nlocal)):
            self.PushD()

        self.curFName = FName

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

def main():
    parser = argparse.ArgumentParser(description='PROCESSING INT VALUES')
    parser.add_argument('path', type=str, help='VIRTUAL MACHINE FILE/FOLDER')

    args = parser.parse_args()
    path = args.path

    if path.endswith(".vm"):  
        codewriter = CodeWriter(path[:-3] + ".asm")
        Translate(path, codewriter)
        print("AFTER TRANSLATION: ", path[:-3] + ".asm")
    else:
        if path.endswith("/"):
            path = path[:-1]
        codewriter = CodeWriter(path + ".asm")
        files = glob.glob("%s/*" % path)

        for file in files:
            if file.endswith(".vm"):
                Translate(file, codewriter)
        print("AFTER TRANSLATION: ", path + ".asm")


def Translate(file, codewriter):
    filename, _ = os.path.splitext(os.path.basename(file))
    codewriter.set_FileNameNew(filename)
    parser = Parser(file)
    parser.getCommand()
    while parser.commands!=None:
        if parser.IdentifyType() == C_ARITHMETIC:
            codewriter.Arithmetic(parser.arg1())
        elif parser.IdentifyType() == C_PUSH:
            codewriter.StackAccess(C_PUSH, parser.arg1(), parser.arg2())
        elif parser.IdentifyType() == C_POP:
            codewriter.StackAccess(C_POP, parser.arg1(), parser.arg2())

        parser.getCommand()


if __name__ == '__main__':
    main()