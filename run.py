from bin_convert import HalfPrecision, Length
from storage import memory, register, variable
from addressing import Access, AddressingMode
from compiler import Instruction


class Except:
    # Handles the execution exceptions by keeping track of the error message,
    # occurrence status, and specialized return values for exceptions

    def __init__(self, msg, occur=True):
        # Initializes the exception with a message and occurrence status
        self.message = msg
        self.occur = occur
        self.ret = None

    def dispMSG(self):
        # Prints the exception message
        print(self.message)

    def isOccur(self):
        # Returns boolean based on if a specific exception has occurred
        return self.occur

    def setReturn(self, value):
        # Sets the return value for the exception, for specific cases
        self.ret = value

    def getReturn(self):
        # Returns the specialized return value for the exception
        return self.ret


class Program:

    # Encode the program text and load instructions into memory
    def __init__(self, program):
        Instruction.encodeProgram(program)

    @staticmethod
    def exception(name, value):
        # Only DivByZero exists for now
        # to add more elif blocks if new exceptions come up
        if name == "DivByZero":
            exc = Except("Division by Zero Error")
            if value[0] == 0 and value[1] == 0:
                exc.setReturn("Infinity")  # dividing 0 by 0
            else:
                exc.setReturn("undefined")  # dividing nonzero by 0
            return exc

    def write(self, dest, src, movecode):
        # Performs the write operation; movecode triggers special pre-write actions.
        if movecode == 1:
            # Save current PC into CR so we can return later
            Access.store("reg", variable.load("CR"), Access.data("PC", ["reg"]))
        elif movecode == 2:
            # Restore CR back into PC to return to the caller
            Access.store("reg", variable.load("PC"), Access.data("CR", ["reg"]))
        elif movecode == 3:
            # Prompt the user using the stored message; replace src with the input value
            src = input(variable.data["MSG"].get(int(src), ""))
        # Store src into dest after any movecode handling
        dest_addr, dest_type = dest
        Access.store(dest_type, dest_addr, src)

    def execute(self, result, opcode):
        # Performs arithmetic (W=1) or a conditional jump (W=0) based on opcode.
        # Returns the computed result for arithmetic; None for jumps.
        val1, val2 = result
        w = int(opcode[1])  # write bit: 1 = arithmetic, 0 = jump
        cat = int(opcode[2:], 2)  # category code selects specific operation

        if w == 1:
            # Arithmetic: select operation by category code
            if cat == 0:
                return int(val1) % int(val2)  # MOD: remainder
            if cat == 1:
                return val1 + val2  # ADD: addition
            if cat == 2:
                return val1 - val2  # SUB: subtraction
            if cat == 3:
                return val1 * val2  # MUL: multiplication
            if cat == 4:
                # DIV: check for division by zero before dividing
                exc = Program.exception("DivByZero", (val1, val2))
                if val2 == 0:
                    exc.dispMSG()
                    return exc.getReturn()  # return 'Infinity' or 'undefined'
                return val1 / val2
        else:
            # Jump: compare JR to 0 and redirect PC to val1 if condition is met.
            # JR holds the result of the last CMP (SUB JR operand), so JR >= 0
            # means the left operand was >= the right operand.
            jr = Access.data("JR", ["reg"])
            cond = {
                0: jr == 0,
                1: jr != 0,
                2: jr < 0,
                3: jr <= 0,
                4: jr > 0,
                5: jr >= 0,
                6: True,
            }
            if cond.get(cat, False):
                Access.store(
                    "reg", variable.load("PC"), val1
                )  # redirect PC to jump target

    def getOp(self, inscode):
        # Gets the effective address and storage type from a 10-bit operand code.
        # Operand code layout: mode(3) + flag(1) + address(6) = 10 bits
        mode = inscode[0:3]  # 3-bit addressing mode
        flag = inscode[3]  # displacement type or sign flag
        addr = int(inscode[4:], 2)  # 6-bit address as integer
        hp = HalfPrecision.hpdec2bin(addr)  # address as Half Precision binary

        if mode == "000":
            return AddressingMode.register(hp)  # register direct
        if mode == "001":
            return AddressingMode.register_indirect(addr)  # register indirect
        if mode == "010":
            return AddressingMode.direct(hp)  # direct memory
        if mode == "011":
            return AddressingMode.indirect(addr)  # indirect memory
        if mode == "110":
            return AddressingMode.autoinc(addr)  # auto-increment
        if mode == "111":
            return AddressingMode.autodec(addr)  # auto-decrement

        if mode == "100":
            # Indexed: displacement from register (flag=0) or memory (flag=1)
            displace = register.load(addr) if flag == "0" else memory.load(addr)
            return AddressingMode.indexed(displace)

        if mode == "101":
            # Indexed: integer displacement (flag=0 = positive, flag=1 = negative)
            displace = addr if flag == "0" else -addr
            return AddressingMode.indexed(displace)

    def run(self):
        # Fetch-decode-execute loop. Runs instructions starting from the address in IR.
        # Stops when it encounters a non-32-bit value or all-zero instruction (EOP/FUNC).
        while True:
            ir_val = Access.data(
                "IR", ["reg"]
            )  # get current instruction address from IR
            inscode = memory.load(ir_val)  # load the 32-bit instruction from memory

            # Stop if the loaded value is not a valid 32-bit binary string
            if not isinstance(inscode, str) or len(inscode) != Length.instrxn:
                break
            # Stop if instruction is all zeros (EOP / FUNC sentinel)
            if set(inscode) == {"0"}:
                break

            # Decode fixed fields of the 32-bit instruction
            opcode = inscode[0:5]  # 5-bit opcode (E + W + Category)
            e = int(opcode[0])  # execute bit
            w = int(opcode[1])  # write bit
            ib = inscode[5]  # immediate bit: 1 = op2 is immediate
            op1 = inscode[6:16]  # operand 1 code (10 bits)
            rb = inscode[16]  # relative bit: 1 = op2 is relative or based
            op2 = inscode[17:27]  # operand 2 code (10 bits)

            # Resolve operand 1 into address, value, and storage type
            res1 = self.getOp(op1)
            op1_addr, op1_val, op1_type = res1 if len(res1) == 3 else (*res1, "mem")

            # Resolve operand 2 based on ib and rb flags
            op2_val = None
            if ib == "1":
                # Immediate: bits 17-31 encode a Half Precision literal; prepend sign bit
                op2_val = AddressingMode.immediate("0" + inscode[17:])
            elif rb == "1":
                # Based or Relative: decode a displacement from mode and flag bits
                mode = op2[0:3]
                flag = op2[3]
                addr = int(op2[4:], 2)
                # Displacement from register or memory when the operand encodes an address source
                if mode in ("000", "001", "100", "101"):
                    displace = register.load(addr) if flag == "0" else memory.load(addr)
                else:
                    # Integer displacement: flag=0 positive, flag=1 negative
                    displace = addr if flag == "0" else -addr
                # Based modes are 000-011, Relative modes are 100-111
                op2_val = (
                    AddressingMode.based(displace)
                    if mode < "100"
                    else AddressingMode.relative(displace)
                )
            else:
                # Normal operand: decode using getOp and extract the value
                res2 = self.getOp(op2)
                op2_val = res2[1]

            # Execute phase: perform arithmetic or jump
            exec_res = self.execute((op1_val, op2_val), opcode) if e == 1 else None

            # Write phase: store the result into the destination
            if w == 1:
                cat = int(opcode[2:], 2)
                movecode = (
                    {1: 1, 2: 2, 3: 3}.get(cat, 0) if e == 0 else 0
                )  # special moves
                src = exec_res if e == 1 else op2_val  # arithmetic or plain move
                self.write((op1_addr, op1_type), src, movecode)

            # Print phase: E=0 and W=0 → PRNT operation
            elif e == 0 and w == 0:
                if int(opcode[2:], 2) == 0:  # category 0 = PRNT
                    msg_key = int(op2_val) if isinstance(op2_val, (int, float)) else None
                    if msg_key is not None and msg_key in variable.data["MSG"]:
                        decoded = Instruction.decodeMSG(variable.data["MSG"][msg_key])
                        if "{}" in decoded:
                            print(decoded.format(op1_val), end="")
                        else:
                            print(decoded, end="")
                            if op1_addr != 0 or op1_type != register:
                                print(op1_val, end="")
                    else:
                        msg = variable.data["MSG"].get(msg_key, str(op1_val))
                        print(Instruction.decodeMSG(str(msg)), end="")

            # Advance fetch: copy PC into IR, then increment PC for the next instruction
            pc_addr = variable.load("PC")
            pc_val = register.load(pc_addr)
            register.store(variable.load("IR"), pc_val)  # IR = PC
            register.store(pc_addr, pc_val + 1)  # PC++


div_zero = Except("Division by Zero", occur=False)

# Prompt for a program file, read the instructions, and then execute the loaded program
if __name__ == "__main__":
    filename = input("Enter filename: ")
    with open(filename, "r") as f:
        program = f.readlines()
    program = [line.strip() for line in program]
    prog = Program(program)
    prog.run()
