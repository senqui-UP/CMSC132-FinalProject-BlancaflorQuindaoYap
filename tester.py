# tester.py
# Tests each layer of the ISA simulator independently.
# Run with: python tester.py

import sys

passed = 0
failed = 0

def test(label, got, expected):
    global passed, failed
    ok = str(got) == str(expected) or got == expected
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"  [{status}] {label}")
        print(f"         got:      {got}")
        print(f"         expected: {expected}")
        return
    print(f"  [{status}] {label}")

def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


# ── Reload storages fresh for each section ─────────────────────────────────────
def reload_all():
    # Force a clean reload of all modules so storage state resets
    for mod in ["bin_convert", "storage", "addressing", "compiler", "run"]:
        if mod in sys.modules:
            del sys.modules[mod]


# ══════════════════════════════════════════════════════════════════════════════
section("1. BinaryFraction & HalfPrecision (bin_convert.py)")
# ══════════════════════════════════════════════════════════════════════════════
from bin_convert import HalfPrecision, Length, BinaryFraction

test("HP: 0 → bin → back",     HalfPrecision.hpbin2dec(HalfPrecision.hpdec2bin(0)),   0.0)
test("HP: 1 → bin → back",     HalfPrecision.hpbin2dec(HalfPrecision.hpdec2bin(1)),   1.0)
test("HP: 5 → bin → back",     HalfPrecision.hpbin2dec(HalfPrecision.hpdec2bin(5)),   5.0)
test("HP: 100 → bin → back",   HalfPrecision.hpbin2dec(HalfPrecision.hpdec2bin(100)), 100.0)
test("HP: -3 → bin → back",    HalfPrecision.hpbin2dec(HalfPrecision.hpdec2bin(-3)),  -3.0)
test("HP binary length is 16", len(HalfPrecision.hpdec2bin(5)),                        16)
test("instrxn length is 32",   Length.instrxn,                                          32)


# ══════════════════════════════════════════════════════════════════════════════
section("2. Storage (storage.py)")
# ══════════════════════════════════════════════════════════════════════════════
from storage import memory, register, variable

test("variable has PC",         "PC" in variable.data,          True)
test("variable has BR",         "BR" in variable.data,          True)
test("variable has A",          "A"  in variable.data,          True)
test("register[PC addr] = 10",  register.load(variable.load("PC")), 10.0)
test("register[BR addr] = 9",   register.load(variable.load("BR")),  9.0)
test("memory store/load int",   (memory.store(0, 42) or memory.load(0)), 42.0)
test("memory store/load str",   (memory.store(0, "hello") or memory.load(0)), "hello")


# ══════════════════════════════════════════════════════════════════════════════
section("3. Access & AddressingMode (addressing.py)")
# ══════════════════════════════════════════════════════════════════════════════
from addressing import Access, AddressingMode
from bin_convert import HalfPrecision

# Access.data
test("Access PC via var→reg",   Access.data("PC", ["reg"]), 10.0)
test("Access BR via var→reg",   Access.data("BR", ["reg"]),  9.0)

# Access.store
Access.store("mem", 5, 99)
test("Access.store to memory",  memory.load(5), 99.0)
Access.store("reg", variable.load("R1"), 7)
test("Access.store to register", register.load(variable.load("R1")), 7.0)

# Immediate
test("Immediate: HP(5) → 5.0", AddressingMode.immediate(HalfPrecision.hpdec2bin(5)), 5.0)

# Direct
memory.store(3, 77)
eff, val = AddressingMode.direct(HalfPrecision.hpdec2bin(3))
test("Direct: addr=3, val=77",  val, 77.0)
test("Direct: eff_addr=3",      eff,  3.0)

# Register
reg_addr = variable.load("R1")
register.store(reg_addr, 55)
eff, val, typ = AddressingMode.register(HalfPrecision.hpdec2bin(reg_addr))
test("Register: val=55",        val, 55.0)

# Register Indirect
memory.store(55, 123)  # register R1 holds 55, memory[55] = 123
eff, val = AddressingMode.register_indirect(reg_addr)
test("Register Indirect: val=123", val, 123.0)

# Auto-increment
register.store(reg_addr, 10)
memory.store(10, 88)
eff, val = AddressingMode.autoinc(reg_addr)
test("Autoinc: val=88",              val, 88.0)
test("Autoinc: reg incremented",     register.load(reg_addr), 11.0)

# Auto-decrement
register.store(reg_addr, 10)
memory.store(9, 77)
eff, val = AddressingMode.autodec(reg_addr)
test("Autodec: val=77",              val, 77.0)
test("Autodec: reg decremented",     register.load(reg_addr), 9.0)

# Indexed
xr_addr = variable.load("XR")
register.store(xr_addr, 77)
memory.store(80, 42)
eff, val = AddressingMode.indexed(3)
test("Indexed XR=77 + 3 = mem[80]", val, 42.0)
test("Indexed: eff_addr=80",        eff, 80.0)

# Relative (PC=10, displace=2 → memory[12])
memory.store(12, 66)
val = AddressingMode.relative(2)
test("Relative: PC+2=mem[12]=66",   val, 66.0)

# Based (BR=9, displace=1 → memory[10])
memory.store(10, 33)
val = AddressingMode.based(1)
test("Based: BR+1=mem[10]=33",      val, 33.0)


# ══════════════════════════════════════════════════════════════════════════════
section("4. Instruction Encoding (compiler.py)")
# ══════════════════════════════════════════════════════════════════════════════
from compiler import Instruction

test("EOP encodes to all zeros",    Instruction.encode("EOP"),  "0" * 32)
test("FUNC encodes to opcode 00001", Instruction.encode("FUNC")[:5], "00001")
test("Any encode is 32 bits",       len(Instruction.encode("MOV A 5")), 32)
test("ADD is 32 bits",              len(Instruction.encode("ADD A B")), 32)
test("MOV ib=1 when immediate",     Instruction.encode("MOV A 5")[5], "1")
test("ADD ib=0 when not immediate", Instruction.encode("ADD A B")[5], "0")

# Decode immediate value back from encoded instruction
code = Instruction.encode("MOV A 5")
imm  = HalfPrecision.hpbin2dec("0" + code[17:])
test("MOV A 5 immediate decodes to 5.0", imm, 5.0)

code = Instruction.encode("MOV B 3")
imm  = HalfPrecision.hpbin2dec("0" + code[17:])
test("MOV B 3 immediate decodes to 3.0", imm, 3.0)

test("decodeMSG dash→space",       Instruction.decodeMSG("Hello-World"), "Hello World")
test("decodeMSG under→tab",        Instruction.decodeMSG("col1_col2"),   "col1\tcol2")
test("decodeMSG newline combo",    Instruction.decodeMSG("line1-_line2"),"line1\nline2")
test("decodeMSG minus word",       Instruction.decodeMSG("minus"),       "-")
test("decodeMSG under word",       Instruction.decodeMSG("under"),       "_")


# ══════════════════════════════════════════════════════════════════════════════
section("5. Except class (run.py)")
# ══════════════════════════════════════════════════════════════════════════════
from run import Except, Program

e = Except("test error")
test("Except: isOccur default True",    e.isOccur(), True)
test("Except: getReturn default None",  e.getReturn(), None)
e.setReturn("Infinity")
test("Except: setReturn works",         e.getReturn(), "Infinity")

e2 = Except("no error", occur=False)
test("Except: occur=False",             e2.isOccur(), False)

div = Program.exception("DivByZero", (0, 0))
test("exception 0/0 = Infinity",        div.getReturn(), "Infinity")
div2 = Program.exception("DivByZero", (5, 0))
test("exception 5/0 = undefined",       div2.getReturn(), "undefined")


# ══════════════════════════════════════════════════════════════════════════════
section("6. Full Program Execution (run.py)")
# ══════════════════════════════════════════════════════════════════════════════
# Each sub-test reloads modules to get a clean memory state
import importlib, sys

def fresh_run(program):
    # Reload all modules for a clean slate, run program, return memory+variable
    for mod in list(sys.modules.keys()):
        if mod in ("bin_convert","storage","addressing","compiler","run"):
            del sys.modules[mod]
    from run import Program
    from storage import memory, variable
    Program(program).run()
    return memory, variable

mem, var = fresh_run(["MOV A 5", "MOV B 3", "ADD A B", "EOP"])
test("MOV+ADD: A = 5+3 = 8",           mem.load(var.load("A")), 8.0)
test("MOV+ADD: B stays 3",             mem.load(var.load("B")), 3.0)

mem, var = fresh_run(["MOV A 10", "MOV B 4", "SUB A B", "EOP"])
test("SUB: A = 10-4 = 6",             mem.load(var.load("A")), 6.0)

mem, var = fresh_run(["MOV A 3", "MOV B 4", "MUL A B", "EOP"])
test("MUL: A = 3*4 = 12",             mem.load(var.load("A")), 12.0)

mem, var = fresh_run(["MOV A 10", "MOV B 2", "DIV A B", "EOP"])
test("DIV: A = 10/2 = 5",             mem.load(var.load("A")), 5.0)

mem, var = fresh_run(["MOV A 10", "MOV B 3", "MOD A B", "EOP"])
test("MOD: A = 10%3 = 1",             mem.load(var.load("A")), 1.0)


# ══════════════════════════════════════════════════════════════════════════════
section("7. Error Handling (run.py)")
# ══════════════════════════════════════════════════════════════════════════════
# Test division by zero handling
mem, var = fresh_run(["MOV A 5", "MOV B 0", "DIV A B", "EOP"])
result = mem.load(var.load("A"))
test("DIV by zero: A = undefined",    result, "undefined")

# Test 0/0 division
mem, var = fresh_run(["MOV A 0", "MOV B 0", "DIV A B", "EOP"])
result = mem.load(var.load("A"))
test("DIV 0/0: A = Infinity",         result, "Infinity")


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
total = passed + failed
print(f"\n{'='*50}")
print(f"  RESULTS: {passed}/{total} passed", "✓" if failed == 0 else f"— {failed} failed")
print(f"{'='*50}\n")
