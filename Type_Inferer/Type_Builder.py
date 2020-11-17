from Tools import visitor
from Tools.Semantic import *
from Parser import ProgramNode, ClassDeclarationNode, AttrDeclarationNode, FuncDeclarationNode

# Visitor encargado de contruir los tipos. Una vez que se conocen los nombres
# de los tipos que intervienen en el codifo COOL, este visitor les annade sus
# metodos y atributos, asi como el tipo padre.

class Type_Builder:
    def __init__(self, Context : Context):
        self.Context = Context
        self.CurrentType = None

        self.Errors = []

        # Construye los tipos builtin
        self.ObjectType = self.Context.get_type('Object')

        self.IOType = self.Context.get_type('IO')
        self.IOType.set_parent(self.ObjectType)

        self.IntType = self.Context.get_type('Int')
        self.IntType.set_parent(self.ObjectType)
        self.IntType.sealed = True

        self.StringType = self.Context.get_type('String')
        self.StringType.set_parent(self.ObjectType)
        self.StringType.sealed = True

        self.BoolType = self.Context.get_type('Bool')
        self.BoolType.set_parent(self.ObjectType)
        self.BoolType.sealed = True

        self.IOType.define_method('out_string', ['x'], [self.StringType], SelfType())
        self.IOType.define_method('out_int', ['x'], [self.IntType], SelfType())
        self.IOType.define_method('in_int', [], [], self.IntType)
        self.IOType.define_method('in_string', [], [], self.StringType)

        self.ObjectType.define_method('abort', [], [], self.ObjectType)
        self.ObjectType.define_method('type_name', [], [], self.StringType)
        self.ObjectType.define_method('copy', [], [], SelfType())

        self.StringType.define_method('lenght', [], [], self.IntType)
        self.StringType.define_method('concat', ['x'], [self.StringType], self.StringType)
        self.StringType.define_method('substr', ['l', 'r'], [self.IntType, self.IntType], self.StringType)

    @visitor.on('node')
    def visit(self, node):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node : ProgramNode):
        for type in node.declarations:
            self.visit(type)

        try:
            self.Context.get_type('Main').get_method('main')
        except SemanticException:
            # Cada programa COOL debe tener una clase MAIN
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Class Main and its method main have to be defined')

    @visitor.when(ClassDeclarationNode)
    def visit(self, node : ClassDeclarationNode):
        self.CurrentType = self.Context.get_type(node.id.lex)

        if node.parent:
            try:
                parent_type = self.Context.get_type(node.parent.lex)
                self.CurrentType.set_parent(parent_type)
            except SemanticException as ex:
                # Existio un error al definir el padre
                self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
                self.CurrentType.set_parent(self.ObjectType)
        else:
            self.CurrentType.set_parent(self.ObjectType)

        for feat in node.features:
            self.visit(feat)

    @visitor.when(AttrDeclarationNode)
    def visit(self, node : AttrDeclarationNode):
        try:
            attr_type = self.Context.get_type(node.type.lex)
        except SemanticException as ex:
            # Existio un error al tratar de obtener el tipo del atributo
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
            attr_type = ErrorType()

        try:
            self.CurrentType.define_attribute(node.id.lex, attr_type)
        except SemanticException as ex:
            # Existio un error al tratar de definir el atributo
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')

    @visitor.when(FuncDeclarationNode)
    def visit(self, node : FuncDeclarationNode):
        param_names, param_types = [], []

        for name, type in node.params:
            try:
                type = self.Context.get_type(type.lex)
            except SemanticException as ex:
                # Existio un error al tratar de obtener el tipo del parametro
                self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
                type = ErrorType()
            else:
                if isinstance(type, SelfType):
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Type "{type.name}" canot be used as parameter type')
                    arg_type = ErrorType()

            param_names.append(name.lex)
            param_types.append(type)

        try:
            return_type = self.Context.get_type(node.type.lex)
        except SemanticException as ex:
            # Existio un error al tratar de obtener el tipo del parametro de retorno
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
            return_type = ErrorType()

        try:
            self.CurrentType.define_method(node.id.lex, param_names, param_types, return_type)
        except SemanticException as ex:
            # Existio un error al tratar de definir el metodo
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
