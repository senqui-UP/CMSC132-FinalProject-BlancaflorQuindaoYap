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
        # Message literal operands are handled as immediates in encode()
        elif operand.startswith('M:'):
            return '0' * 10
        # Direct Memory (literal memory address)
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
        # Variable name direct memory (A-H, B1-8, etc.)
        else:
            try:
                memaddr = variable.load(operand)
                mode = '010'
                addr = bin(int(memaddr))[2:].zfill(7)
                return (mode + addr).zfill(10)
            except Exception:
                pass
        return '0'.zfill(10)
    @staticmethod
    def encode(inst):
        inst = inst.strip()
        if inst == '':
            return '0' * 32
        parts = inst.split()
        op = parts[0].upper()
        if op == 'FUNC':
            return '0' * 32
        opcode = ''
        for i in range(len(operations)):
            if op in operations[i]:
                opcode = operationCodes[i]
                break

        ib = '0'
        rb = '0'
        op1 = '0' * 10
        op2 = '0' * 15

        # Support pure message printing
        if op == 'PRNT' and len(parts) == 2 and parts[1].startswith('M:'):
            ib = '1'
            op2 = Instruction.encodeImmediate(parts[1])
        else:
            if len(parts) > 1:
                op1 = Instruction.encodeOp(parts[1])
            if len(parts) > 2:
                operand = parts[2]
                if operand.startswith('M:') or Instruction.isImmediateOperand(operand):
                    ib = '1'
                    op2 = Instruction.encodeImmediate(operand)
                else:
                    rb = '0'
                    op2 = Instruction.encodeOp(operand) + '0' * 5

        inscode = opcode + ib + op1 + rb + op2
        return inscode

    @staticmethod
    def isImmediateOperand(operand):
        try:
            float(operand)
            return True
        except Exception:
            return False

    @staticmethod
    def encodeImmediate(operand):
        if isinstance(operand, str) and operand.startswith('M:'):
            message = operand[2:]
            index = variable.data.get('MI', 0)
            variable.data['MSG'][index] = message
            variable.data['MI'] = index + 1
            value = index
        else:
            try:
                value = float(operand)
            except Exception:
                value = 0
        hpbin = HalfPrecision.hpdec2bin(value)
        return hpbin[1:]
    @staticmethod
    def encodeProgram(program):
        # Load the program starting at the current instruction address (IR),
        # with PC already pointing to the next instruction.
        pc = register.load(variable.load('IR'))
        for inst in program:
            inst = inst.strip()
            if inst == '':
                continue
            if inst.startswith('x'):
                continue
            code = Instruction.encode(inst)
            memory.store(pc, code)
            pc += 1

