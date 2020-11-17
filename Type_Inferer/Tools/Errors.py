'''
Las clases que representan los errores en el codigo,
se les define la propiedad str para que impriman
el error correspondiente
'''

class Error:
    def __init__(self, line = None, column = None):
        self.line = line
        self.column = column
    def __str__(self):
        raise NotImplementedError()
    def __repr__(self):
        raise NotImplementedError()

class UnknownError(Error):
    def __str__(self):
        return f'Unknown Token at line {self.line}, column {self.column}'
    def __repr__(self):
        return f'Unknown Token at line {self.line}, column {self.column}'

class ExpectedError(Error):
    def __init__(self, line = None, column = None, Argument = None):
        super().__init__(line, column)
        self.Argument = Argument
    def __str__(self):
        return f'Expected {self.Argument} at line {self.line}, column {self.column}'
    def __repr__(self):
        return f'Expected {self.Argument} at line {self.line}, column {self.column}'

class UnresolvedReferenceError(ExpectedError):
    def __str__(self):
        return f'Unresolved reference {self.Argument} at line {self.line}, column {self.column}'
    def __repr__(self):
        return f'Unresolved reference {self.Argument} at line {self.line}, column {self.column}'
class UnexpectedError(ExpectedError):
    def __str__(self):
        return f'Unexpected {self.Argument} at line {self.line}, column {self.column}'
    def __repr__(self):
        return f'Unexpected {self.Argument} at line {self.line}, column {self.column}'