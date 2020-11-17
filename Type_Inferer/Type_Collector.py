from Tools import visitor
from Tools.Semantic import *
from Parser import ProgramNode, ClassDeclarationNode

# Visitor encargado de coleccionar los nombres de las clases que se definen
# en el cosigo del programa COOL, chequea ademas que no se redeclaren e
# incluye los tipos builtin dentro del contexto

class Type_Collector:
    def __init__(self):
        self.Errors = []

        self.Context = Context()

        self.Context.add_type(AutoType())
        self.Context.add_type(SelfType())

        self.Context.create_type('Object')
        self.Context.create_type('String')
        self.Context.create_type('IO')
        self.Context.create_type('Int')
        self.Context.create_type('Bool')

    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node : ProgramNode):
        for type in node.declarations:
            self.visit(type)

    @visitor.when(ClassDeclarationNode)
    def visit(self, node : ClassDeclarationNode):
        try:
            self.Context.create_type(node.id.lex)
        except SemanticException as ex:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
