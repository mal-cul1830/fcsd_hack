import sys
import os
comp = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "!D": "0001101",
    "!A": "0110001",
    "-D": "0001111",
    "-A": "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M": "1110000",
    "!M": "1110001",
    "-M": "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101"
    }


dest = {
    "null": "000",
    "M": "001",
    "D": "010",
    "A": "100",
    "MD": "011",
    "AM": "101",
    "AD": "110",
    "AMD": "111"
    }


jump = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111"
    }

vars = {}
symbols = {
    'R0': 0,
    'R1': 1,
    'R2': 2,
    'R3': 3,
    'R4': 4,
    'R5': 5,
    'R6': 6,
    'R7': 7,
    'R8': 8,
    'R9': 9,
    'R10': 10,
    'R11': 11,
    'R12': 12,
    'R13': 13,
    'R14': 14,
    'R15': 15,
    'SP': 0,
    'LCL': 1,
    'ARG': 2,
    'THIS': 3,
    'THAT': 4,
    'SCREEN': 16384,
    'KBD': 24576
}

def make_destination_command(dest_code):
    dest_bin = []
    for f in 'ADM':
      dest_bin.append(str(int(f in dest_code)))
    return ''.join(dest_bin)

def readfile():
    filename = sys.argv[1]
    with open(filename) as f:
      filecontent = f.read()

    #get the lines from the asm code
    lines = filecontent.split('\n')
    lines = [l.strip() for l in lines if l]
    lines = [l.split(' ')[0] for l in lines if l[:2] != '//'] #reading all asm lines that are not comments 

    return lines, filename

#assigning variables the memory locations after location 15
def assignMemory(vars, usedmem):
    loc = 16
    for var in vars:
        if symbols.get(var):#checking if the variable is already an index in symbols
            continue
        while loc in usedmem:
          loc+=1
        usedmem.add(loc)#adding the new location to the used memory
        symbols[var] = loc #associating the given memory address to the variable name
        loc+=1

def parseForSymbols(codeasm):
    line_count = 0
    usedmem = set(symbols.values())
    vars = []
    for line in codeasm:
        if line[0] == '@':
            line_count+=1
            address = line[1:].split(' ')[0]
            print(line[1], "line")
            if line[1].isdigit():
                address = int(address)
                usedmem.add(address)
            else:
                if address in set(vars):
                    continue
                else:
                    vars.append(address)
        elif line[0] == '(':
            bookmark = line[1:-1]
            symbols[bookmark] = line_count
        else:
            line_count+=1

    temp = []
    for var in vars:
      if var not in symbols:
        temp.append(var)
    vars = temp
    assignMemory(vars, usedmem)

def assemble(codeasm):
    command_list = []
    for line in codeasm:
        if line[:2] == '//' or line[0] == '(':
            continue
        if line[0] == '@':

            address = line[1:].split(' ')[0]
            if line[1].isdigit():
                address = int(address)
                command_list.append(f'{address:b}'.zfill(16))
                #print("A", command_list)
            else:
                command_list.append(f'{symbols[address]:b}'.zfill(16))
                #print("A", command_list)

        else:
            #print(line)
            jumppart = line.split(';')
            #print(jumppart)
            if len(jumppart) > 1:
              jumps = jumppart[-1].strip()
              jumps = jump[jumps]
              line=jumppart[0]
            else:
              jumps = "000"

            comppart = line.split('=')
            #print(comppart)
            if len(comppart)>1:
              comps = comp[comppart[-1].strip()]
              #print(comp)
              line = comppart[0]
            else:
              comps = "0"*7
            
            destpart = line
            dests = make_destination_command(destpart)
            #print(dests)

            command = '111' + comps + dests + jumps
            #print(command, "C")
            command_list.append(command)

    return command_list

def createHackFile(commands, filename):
    fullbinary = '\n'.join(commands)
    hackfile = open(filename.split(".asm")[0] + ".hack", 'w')
    hackfile.write(fullbinary)
    hackfile.close()

if __name__ == '__main__':
    codeasm, filename = readfile()
    parseForSymbols(codeasm)
    binaryCommands = assemble(codeasm)
    print("Writing into "+filename.split('.asm')[0]+'.hack')
    createHackFile(binaryCommands, filename)