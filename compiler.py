from bin_convert import HalfPrecision, Length
from storage import memory, register, variable

operations = [
    ['PRNT'],
    ['EOP'],
    ['FUNC'],
    ['MOV'],
    ['ADDPC'],
    ['CALL'],
    ['RET'],
    ['SCAN'],
    ['JEQ'],
    ['JNE'],
    ['JLT'],
    ['JLE'],
    ['JGT'],
    ['JGE'],
    ['JMP'],
    ['MOD'],
    ['ADD'],
    ['CB'],
    ['CF'],
    ['SUB'],
    ['CMP'],
    ['MUL'],
    ['DIV']
]

operationCodes = [
    '00000',  # PRNT
    '00001',  # EOP
    '00001',  # FUNC (same as EOP per spec)
    '01000',  # MOV
    '01000',  # ADDPC (same category as MOV)
    '01001',  # CALL
    '01010',  # RET
    '01011',  # SCAN
    '10000',  # JEQ
    '10001',  # JNE
    '10010',  # JLT
    '10011',  # JLE
    '10100',  # JGT
    '10101',  # JGE
    '10110',  # JMP
    '11000',  # MOD
    '11001',  # ADD
    '11001',  # CB (same category as ADD)
    '11001',  # CF (same category as ADD)
    '11010',  # SUB
    '11010',  # CMP (same category as SUB)
    '11011',  # MUL
    '11100'   # DIV
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
        # Special Registers: PC, ACC, JR, CR, BR, XR, IR all live in the register file
        elif operand in ('PC', 'ACC', 'JR', 'CR', 'BR', 'XR', 'IR'):
            mode = '000'
            addr = bin(int(variable.load(operand)))[2:].zfill(7)
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

        # EOP and FUNC are end-of-program sentinels → all zeros
        if op in ('EOP', 'FUNC'):
            return '0' * 32

        # CMP: rewrite as SUB JR <operand> per PDF spec
        # CMP A means JR = JR - A; to compare A vs B: MOV JR A then CMP B
        if op == 'CMP':
            op = 'SUB'
            parts = ['SUB', 'JR', parts[1]]

        # CB / CF: rewrite as ADD block BR so the block stores the current BR address
        if op in ('CB', 'CF'):
            op = 'ADD'
            parts = ['ADD', parts[1], 'BR']

        opcode = ''
        for i in range(len(operations)):
            if op in operations[i]:
                opcode = operationCodes[i]
                break

        ib = '0'
        rb = '0'
        op1 = '0' * 10
        op2 = '0' * 15

        # PRNT with only a message (no variable)
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
        # Two-pass compiler:
        # Pass 1: scan all instructions to calculate exact memory addresses for CB/CF blocks
        # Pass 2: encode all instructions in order; CB/CF become NOPs (JR=JR) at their address
        start = register.load(variable.load('IR'))  # first instruction memory address
        in_comment = False

        # Pass 1: calculate addresses 
        addr = start
        clean = []      # cleaned instruction list (no blanks/comments)
        for inst in program:
            inst = inst.strip()
            if not inst: continue
            if inst[0] == 'z':
                in_comment = not in_comment
                continue
            if inst[0] == 'x' or in_comment: continue
            op = inst.split()[0].upper()
            if op in ('CB', 'CF'):
                # block body starts at the instruction AFTER this CB/CF
                blk_name = inst.split()[1]
                blk_slot = variable.load(blk_name)      # get the memory slot for this block (e.g. 57 for B1)
                memory.store(blk_slot, addr + 1)          # store jump target address into that memory slot
            clean.append(inst)
            addr += 1   # every instruction takes one memory slot

        # ── Pass 2: encode and store ──────────────────────────────────────────
        for i, inst in enumerate(clean):
            op = inst.split()[0].upper()
            if op in ('CB', 'CF'):
                code = Instruction.encode('MOV JR JR')  # NOP: block marker, no real action
            else:
                code = Instruction.encode(inst)
            memory.store(start + i, code)