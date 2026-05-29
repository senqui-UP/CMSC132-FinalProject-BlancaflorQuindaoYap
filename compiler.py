from bin_convert import HalfPrecision, Length
from storage import memory, register, variable

operations = [
    ['PRNT', 'EOP', 'FUNC'],
    ['MOV', 'ADDPC', 'CALL', 'RET', 'SCAN'],
    ['JEQ', 'JNE', 'JLT', 'JLE', 'JGT', 'JGE', 'JMP'],
    ['MOD', 'ADD', 'CB', 'CF'],
    ['SUB', 'CMP'],
    ['MUL'],
    ['DIV']
]
operationCodes = [
    '00000',
    '01000',
    '10000',
    '11001',
    '11010',
    '11011',
    '11100'
]
class Instruction:
    @staticmethod
    def decodeMSG(msg):
        msg = msg.replace('-_', '\n')
        msg = msg.replace('_', '\t')
        msg = msg.replace('-', ' ')
        msg = msg.replace('minus', '-')
        msg = msg.replace('under', '_')
        return msg
    @staticmethod
    def encodeOp(operand):
        operand = operand.strip()
        # Immediate value
        try:
            value = float(operand)
            return HalfPrecision.hpdec2bin(value).zfill(10)
        except:
            pass
        mode = ''
        addr = ''
        # Register Addressing
        if operand.startswith('R'):
            mode = '000'
            regnum = operand.replace('R', '')
            addr = bin(int(regnum))[2:].zfill(7)
            return (mode + addr).zfill(10)
        # Special Registers
        elif operand == 'PC':
            mode = '000'
            addr = bin(variable.load('PC'))[2:].zfill(7)
            return (mode + addr).zfill(10)
        elif operand == 'ACC':
            mode = '000'
            addr = bin(variable.load('ACC'))[2:].zfill(7)
            return (mode + addr).zfill(10)
        # Direct Memory
        elif operand.startswith('M'):
            mode = '010'
            memaddr = operand.replace('M', '')
            addr = bin(int(memaddr))[2:].zfill(7)
            return (mode + addr).zfill(10)
        # Register Indirect
        elif '(' in operand and ')' in operand:
            inside = operand.replace('(', '').replace(')', '')
            # Auto Increment
            if '+' in inside:
                mode = '110'
                inside = inside.replace('+', '')
            # Auto Decrement
            elif '-' in inside:
                mode = '111'
                inside = inside.replace('-', '')
            # Register Indirect
            elif inside.startswith('R'):
                mode = '001'
            # Indirect
            else:
                mode = '011'
            if inside.startswith('R'):
                regnum = inside.replace('R', '')
                addr = bin(int(regnum))[2:].zfill(7)
            else:
                addr = bin(int(inside))[2:].zfill(7)
            return (mode + addr).zfill(10)
        return '0'.zfill(10)
    @staticmethod
    def encode(inst):
        inst = inst.strip()
        if inst == '':
            return '0'.zfill(32)
        parts = inst.split()
        op = parts[0].upper()
        if op == 'FUNC':
            return '0'.zfill(32)
        opcode = ''
        for i in range(len(operations)):
            if op in operations[i]:
                opcode = operationCodes[i]
                break
        op1 = ''
        op2 = ''
        if len(parts) > 1:
            op1 = Instruction.encodeOp(parts[1])
        if len(parts) > 2:
            op2 = Instruction.encodeOp(parts[2])
        inscode = opcode + op1 + op2
        return inscode.zfill(32)
    @staticmethod
    def encodeProgram(program):
        pc = variable.load('PC')
        for inst in program:
            inst = inst.strip()
            if inst == '':
                continue
            if inst.startswith('x'):
                continue
            code = Instruction.encode(inst)
            memory.store(pc, code)
            pc += 1

