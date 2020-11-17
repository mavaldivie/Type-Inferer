
from Tools import visitor
from Parser import ProgramNode, ClassDeclarationNode, AttrDeclarationNode, FuncDeclarationNode,\
                   IfThenElseNode, WhileLoopNode, BlockNode, LetInNode, CaseOfNode,\
                   AssignNode, LessEqualNode, LessNode, EqualNode, ArithmeticNode,\
                   NotNode, IsVoidNode, ComplementNode, FunctionCallNode, MemberCallNode, NewNode,\
                   IntegerNode, IdNode, StringNode, BoolNode
from Tools.Semantic import Context, Scope, SelfType, AutoType, SemanticException, ErrorType


# Este es el visitor encargado de terminar el chequeo semantico.
# Revisa la compatibilidad de tipos, la compatibilidad en la herencia,
# que las variables hayan sido previamente definidas, asi como los
# metodos y atributos de clase, crea el scope para las variables, el
# cual sera rehusado para inferir las variables que se requieran.
# Observar que cada vez que el visitor llama recursivamente crea un scope
# hijo en el scope actual, esto se hace para que las variables previamente
# declaradas en ambitos hermanos no sean utiles en el ambito actual.

class Type_Checker:

    def __init__(self, Context : Context):
        self.Context = Context
        self.Errors = []
        self.Current_Type = None
        self.Current_Method = None

        self.Object_Type = self.Context.get_type('Object')
        self.IO_Type = self.Context.get_type('IO')
        self.String_Type = self.Context.get_type('String')
        self.Int_Type = self.Context.get_type('Int')
        self.Bool_Type = self.Context.get_type('Bool')

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node : ProgramNode, scope : Scope = None):
        scope = Scope()
        for declaration in node.declarations:
            self.visit(declaration, scope.create_child())
        return scope

    @visitor.when(ClassDeclarationNode)
    def visit(self, node : ClassDeclarationNode, scope : Scope):
        self.Current_Type = self.Context.get_type(node.id.lex)

        parent = self.Current_Type.parent
        # Revisa que no haya herencia ciclica
        while parent:
            if parent == self.Current_Type:
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Type {self.Current_Type.name} has cyclic heritage')
                self.Current_Type.parent = self.Object_Type
                break
            parent = parent.parent

        # Incluyo cada uno de los atributos de la clase
        for att in self.Current_Type.attributes:
            scope.define_variable(att.name, att.type)

        for feature in node.features:
            self.visit(feature, scope.create_child())
        node.static_type = self.Current_Type

    @visitor.when(AttrDeclarationNode)
    def visit(self, node : AttrDeclarationNode, scope : Scope):
        expr = node.expression
        if expr:
            self.visit(expr, scope.create_child())
            expr_type = expr.static_type

            attr = self.Current_Type.get_attribute(node.id.lex)
            node_type = self.Current_Type if isinstance(attr.type, SelfType) else attr.type

            # Chequeo compatibilidad de tipos
            if not expr_type.inherits_from(node_type):
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Incompatible types {expr_type.name} and {node_type.name}')

        node.static_type = self.Current_Type

    @visitor.when(FuncDeclarationNode)
    def visit(self, node : FuncDeclarationNode, scope : Scope):
        self.Current_Method = self.Current_Type.get_method(node.id.lex)

        scope.define_variable('self', self.Current_Type)

        # Defino cada uno de los parametros de metodo
        for pname, ptype in zip(self.Current_Method.param_names, self.Current_Method.param_types):
            scope.define_variable(pname, ptype)

        # Chequeo consistencia en el cuerpo del metodo
        self.visit(node.body, scope.create_child())

        expr_type = node.body.static_type
        return_type = self.Current_Method.return_type

        # Chequeo consistencia entre el tipo de retorno definido y el tipo de retorno
        # del cuerpo del metodo
        if not expr_type.inherits_from(return_type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Incompatible types {expr_type.name} and {return_type.name}')
        node.static_type = return_type

    @visitor.when(IfThenElseNode)
    def visit(self, node : IfThenElseNode, scope : Scope):
        # Chequeo consistencia en la condicion del if
        self.visit(node.condition, scope.create_child())

        condition_type = node.condition.static_type
        # Chequeo que el tipo de la condicion sea booleano
        if not condition_type.inherits_from(self.Bool_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Incompatible types {condition_type.name} and {self.Bool_Type.name}')

        # Chqueo consistencia en las expresiones del then y el else
        self.visit(node.if_body, scope.create_child())
        self.visit(node.else_body, scope.create_child())

        if_type = node.if_body.static_type
        else_type = node.else_body.static_type

        # Mi tipo es el ancestro comun a los tipos del then y el else
        node.static_type = if_type.type_union(else_type)


    @visitor.when(WhileLoopNode)
    def visit(self, node : WhileLoopNode, scope : Scope):
        self.visit(node.condition, scope.create_child())
        condition_type = node.condition.static_type

        # Chequeo que la condicion sea de tipo booleano
        if not condition_type.inherits_from(self.Bool_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Incompatible types {condition_type.name} and {self.Bool_Type.name}')

        # Chequeo consistencias en el cuerpo del while
        self.visit(node.body, scope.create_child())

        node.static_type = node.body.static_type

    @visitor.when(BlockNode)
    def visit(self, node : BlockNode, scope : Scope):

        # Chequeo consistencias en cada una de las instrucciones del cuerpo del bloque
        for expr in node.expressions:
            self.visit(expr, scope.create_child())

        node.static_type = node.expressions[-1].static_type

    @visitor.when(LetInNode)
    def visit(self, node : LetInNode, scope : Scope):
        for id, type, expr in node.let_body:
            # Por cada una de las declaraciones del let
            try:
                type = self.Context.get_type(type.lex)
            except SemanticException as ex:
                # Chequeo que el tipo exista
                self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
                type = ErrorType()

            # Si es Self_Type tomo el tipo correspondiente
            type = self.Current_Type if isinstance(type, SelfType) else type

            child = scope.create_child()
            if expr:
                # Chequeo consistencias en la declaracion y la compatibilidad de tipos
                self.visit(expr, child)
                if not expr.static_type.inherits_from(type):
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Incompatible types {type.name} and {expr.static_type.name}')

            # Defino la variable
            scope.define_variable(id.lex, type)

        # Chequeo consistencias en el cuerpo del let in
        self.visit(node.in_body, scope.create_child())
        node.static_type = node.in_body.static_type

    @visitor.when(CaseOfNode)
    def visit(self, node : CaseOfNode, scope : Scope):
        # Chequeo consistencias en el case
        self.visit(node.expression, scope.create_child())

        node.static_type = None
        for id, type, expr in node.branches:
            # Por cada instruccion en el cuerpo del case-of
            try:
                type = self.Context.get_type(type.lex)
            except SemanticException as ex:
                # Chequeo que el tipo exista
                self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
                type = ErrorType()

            # Chequeo que no sea un tipo especial
            if isinstance(type, SelfType) or isinstance(type, AutoType):
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Type {type.name} cannot be used as a case branch type')

            child = scope.create_child()
            # Declaro la variable y chequeo consistencias en la expresion
            child.define_variable(id.lex, type)
            self.visit(expr, child)

            node.static_type = node.static_type.type_union(expr.static_type) if node.static_type else expr.static_type

    @visitor.when(AssignNode)
    def visit(self, node : AssignNode, scope : Scope):
        # Chequeo consistencias en la expresion
        self.visit(node.expression, scope.create_child())
        expr_type = node.expression.static_type

        # Chequeo que la variable este declarada y que su tipo sea valido
        if scope.is_defined(node.id.lex):
            var_type = scope.find_variable(node.id.lex).type
            if isinstance(var_type, SelfType):
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Self type variables are readonly')
            elif not expr_type.inherits_from(var_type):
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Incompatible types {var_type.name} and {expr_type.name}')
        else:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undeclared variable {node.id.lex}')

        node.static_type = expr_type

    @visitor.when(NotNode)
    def visit(self, node : NotNode, scope : Scope):
        # Chequeo la consistencia de la expresion
        self.visit(node.expression, scope.create_child())

        # Chequeo que la expresion sea booleana
        if not node.expression.static_type.inherits_from(self.Bool_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Incompatible types {node.expression.static_type.name} '
                               f'and {self.Bool_Type.name}')

        node.static_type = self.Bool_Type

    @visitor.when(LessEqualNode)
    def visit(self, node : LessEqualNode, scope : Scope):
        # Chequeo la consistencia de ambos miembros
        self.visit(node.left, scope.create_child())
        self.visit(node.right, scope.create_child())
        left_type = node.left.static_type
        right_type = node.right.static_type

        # Chequeo que ambos miembros posean tipo int
        if not left_type.inherits_from(self.Int_Type) or not right_type.inherits_from(self.Int_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')

        node.static_type = self.Bool_Type

    @visitor.when(LessNode)
    def visit(self, node: LessNode, scope: Scope):
        # Chequeo la consistencia de ambos miembros
        self.visit(node.left, scope.create_child())
        self.visit(node.right, scope.create_child())
        left_type = node.left.static_type
        right_type = node.right.static_type

        # Chequeo que ambos miembros posean tipo int
        if not left_type.inherits_from(self.Int_Type) or not right_type.inherits_from(self.Int_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')

        node.static_type = self.Bool_Type

    @visitor.when(EqualNode)
    def visit(self, node: EqualNode, scope: Scope):
        # Chequeo la consistencia de ambos miembros
        self.visit(node.left, scope.create_child())
        self.visit(node.right, scope.create_child())
        left_type = node.left.static_type
        right_type = node.right.static_type

        # Chequeo que ambos miembros posean tipos comparables
        if isinstance(left_type, AutoType) or isinstance(right_type, AutoType):
            pass
        elif left_type.inherits_from(self.Int_Type) ^ right_type.inherits_from(self.Int_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')
        elif left_type.inherits_from(self.String_Type) ^ right_type.inherits_from(self.String_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')
        elif left_type.inherits_from(self.Bool_Type) ^ right_type.inherits_from(self.Bool_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')

        node.static_type = self.Bool_Type

    @visitor.when(ArithmeticNode)
    def visit(self, node : ArithmeticNode, scope : Scope):
        # Chequeo la consistencia de ambos miembros
        self.visit(node.left, scope.create_child())
        self.visit(node.right, scope.create_child())
        left_type = node.left.static_type
        right_type = node.right.static_type

        # Chequeo que ambos miembros posean tipo int
        if not left_type.inherits_from(self.Int_Type) or not right_type.inherits_from(self.Int_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {left_type.name} and {right_type.name}')

        node.static_type = self.Int_Type

    @visitor.when(IsVoidNode)
    def visit(self, node : IsVoidNode, scope : Scope):
        # Chequeo la consistencia de la expresion
        self.visit(node.expression, scope.create_child())
        node.static_type = self.Bool_Type

    @visitor.when(ComplementNode)
    def visit(self, node : ComplementNode, scope : Scope):
        # Chequeo la consistencia de la expresion
        self.visit(node.expression, scope.create_child())

        # Chequeo que la expresion sea de tipo booleana
        if not node.expression.static_type.inherits_from(self.Int_Type):
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Undefined operation for {node.expression.static_type.name}')

        node.static_type = self.Int_Type

    @visitor.when(FunctionCallNode)
    def visit(self, node : FunctionCallNode, scope : Scope):
        # Chequeo la consistencia de la expresion a la cual se le pide la funcion
        self.visit(node.obj, scope.create_child())
        obj_type = node.obj.static_type

        try:
            if node.type:
                # Chequeo que el tipo exista
                try:
                    node_type = self.Context.get_type(node.type.lex)
                except SemanticException as ex:
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
                    node_type = ErrorType()

                # Chequeo que el tipo no sea un tipo especial
                if isinstance(node_type, SelfType) or isinstance(node_type, AutoType):
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Type {node_type.name} cannot be used as a dispatch')

                # Chequeo que los tipos sean compatibles
                if not obj_type.inherits_from(node_type):
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Incompatible types {node_type.name} '
                                       f'and {obj_type.name}')

                obj_type = node_type


            if isinstance(obj_type, AutoType):
                # Si el tipo es Auto_Type no se puede conocer si posee el metodo
                self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                   f'Type {obj_type.name} cannot be used as a dispatch')
                return_type = ErrorType()
                obj_method = None
            else:
                obj_method = obj_type.get_method(node.id.lex)
                return_type = obj_type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type

        except SemanticException as ex:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
            return_type = ErrorType()
            obj_method = None

        # Chequeo consistencias en los argumentos con los que se llama al metodo
        for arg in node.args:
            self.visit(arg, scope.create_child())

        if obj_method and len(node.args) == len(obj_method.param_types):
            for arg, param_type in zip(node.args, obj_method.param_types):
                if not arg.static_type.inherits_from(param_type):
                    # Chequeo compatibilidad de tipos entre los argumentos
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Incompatible types {arg.static_type.name} '
                                       f'and {param_type.name}')

        elif obj_method:
            # Chequeo que la cantidad de argumentos sea igual a las solicitadas por el metodo
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Method {node.id.lex} cannot be dispatched')

        node.static_type = return_type


    @visitor.when(MemberCallNode)
    def visit(self, node : MemberCallNode, scope : Scope):
        # Chequeo que el metodo exista en el tipo actual
        try:
            obj_method = self.Current_Type.get_method(node.id.lex)
            return_type = self.Current_Type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticException as ex:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
            obj_method = None
            return_type = ErrorType()

        # Chequeo la consistencia en los argumentos
        for arg in node.args:
            self.visit(arg, scope.create_child())

        if obj_method and len(node.args) == len(obj_method.param_types):
            # Chequeo la compatibiidad entre los tipos de los argumentos
            for arg, param_type in zip(node.args, obj_method.param_types):
                if not arg.static_type.inherits_from(param_type):
                    self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                                       f'Incompatible types {arg.static_type.name} '
                                       f'and {param_type.name}')

        elif obj_method:
            # Chequeo que la cantidad de argumentos coincida con los que requiere el metodo
            self.Errors.append(f'Error on line {node.line}, column {node.column}: '
                               f'Method {node.id.lex} cannot be dispatched')

        node.static_type = return_type

    @visitor.when(NewNode)
    def visit(self, node : NewNode, scope : Scope):
        # Chequeo que el tipo exista
        try:
            type = self.Context.get_type(node.type.lex)
        except SemanticException as ex:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: {ex.text}')
            type = ErrorType()

        node.static_type = type

    @visitor.when(IntegerNode)
    def visit(self, node : IntegerNode, scope : Scope):
        node.static_type = self.Int_Type

    @visitor.when(StringNode)
    def visit(self, node: StringNode, scope: Scope):
        node.static_type = self.String_Type

    @visitor.when(BoolNode)
    def visit(self, node: BoolNode, scope: Scope):
        node.static_type = self.Bool_Type

    @visitor.when(IdNode)
    def visit(self, node: IntegerNode, scope: Scope):
        # Chequeo que la variable exista
        if scope.is_defined(node.token.lex):
            node.static_type = scope.find_variable(node.token.lex).type
        else:
            self.Errors.append(f'Error on line {node.line}, column {node.column}: Undefined variable {node.token.lex}')
            node.static_type = ErrorType()
