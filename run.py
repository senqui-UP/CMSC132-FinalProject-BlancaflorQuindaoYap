from bin_convert import HalfPrecision
from storage import memory, register, variable


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
    # __init__ here
    # write here
    # execute here
    # getOp here
    # run here

    @staticmethod
    def exception(name, value):
        # Only DivByZero exists for now
        # to add more elif blocks if new exceptions come up
        if name == 'DivByZero':
            exc = Except('Division by Zero Error')
            if value[0] == 0 and value[1] == 0:
                exc.setReturn('Infinity')               # dividing 0 by 0
            else:
                exc.setReturn('undefined')              # dividing nonzero by 0
            return exc

    # file-reading and program instantiation below this class