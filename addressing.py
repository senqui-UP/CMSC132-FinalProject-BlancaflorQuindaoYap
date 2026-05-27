from bin_convert import HalfPrecision
from storage import memory, register, variable


class Access:
    
    @staticmethod
    def data(addr, flow):
        # Loads the value that follows the flow from the specified address
        storages = {'var': variable, 'reg': register, 'mem': memory}
        value = storages['var'].load(addr)
        for storage in flow:
            value = storages[storage].load(value)
        return value

    @staticmethod
    def store(typ, addr, value):
        # Store the value to the specified storage (memory or register) and address
        storages = {'reg': register, 'mem': memory}
        storages[typ].store(addr, value)


class AddressingMode:

    @staticmethod
    def immediate(var):
        # Returns value of converted var from Half Precision binary format to decimal
        return HalfPrecision.hpbin2dec(var)

    @staticmethod
    def relative(displace):
        # Gets the value of PC and add it to displace
        # Returns value at the effective address (PC + displace)
        pc = Access.data('PC', ['reg'])
        eff_addr = pc + displace
        value = memory.load(eff_addr)
        return value

    @staticmethod
    def based(displace):
        # Gets the address of BR and add it to displace
        # Returns value at the effective address (BR + displace)
        br_addr = Access.data('BR', ['reg'])
        eff_addr = br_addr + displace
        value = memory.load(eff_addr)
        return value

    @staticmethod
    def indexed(displace):
        # Gets the value of XR and add it to displace
        # Returns effective address and value it's pointing to (XR + displace)
        xr = Access.data('XR', ['reg'])
        eff_addr = xr + displace
        value = memory.load(eff_addr)
        return eff_addr, value

    @staticmethod
    def register(reg_addr):
        # Converts reg_addr from Half Precision binary format to decimal
        # Returns effective address, value in register, and storage type (register)
        eff_addr = HalfPrecision.hpbin2dec(reg_addr)
        value = register.load(eff_addr)
        return eff_addr, value, register

    @staticmethod
    def register_indirect(reg_addr):
        # Gets value based on reg_addr directly, no HP conversion specified
        # Returns effective address and value it's pointing to
        mem_addr = register.load(reg_addr)
        value = memory.load(mem_addr)
        return mem_addr, value

    @staticmethod
    def direct(var_addr):
        # Converts var_addr from Half Precision binary format to decimal
        # Returns effective address and value it's pointing to
        eff_addr = HalfPrecision.hpbin2dec(var_addr)
        value = memory.load(eff_addr)
        return eff_addr, value

    @staticmethod
    def indirect(var_addr):
        # Gets value based on var_addr directly, no HP conversion specified
        # Returns effective address and value it's pointing to
        mem_addr = memory.load(var_addr)
        value = memory.load(mem_addr)
        return mem_addr, value

    @staticmethod
    def autoinc(reg_addr):
        # Get value based on reg_addr, then increment register value by 1
        # Returns effective address and value it's pointing to
        mem_addr = register.load(reg_addr)
        value = memory.load(mem_addr)
        register.store(reg_addr, mem_addr + 1)
        return mem_addr, value

    @staticmethod
    def autodec(reg_addr):
        # Decrement register value by 1, then get value based on reg_addr
        # Returns effective address and value it's pointing to
        mem_addr = register.load(reg_addr)
        mem_addr -= 1
        register.store(reg_addr, mem_addr)
        value = memory.load(mem_addr)
        return mem_addr, value