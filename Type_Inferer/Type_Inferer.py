
from Tools import visitor
from Parser import ProgramNode, ClassDeclarationNode, AttrDeclarationNode, FuncDeclarationNode,\
                   IfThenElseNode, WhileLoopNode, BlockNode, LetInNode, CaseOfNode,\
                   AssignNode, LessEqualNode, LessNode, EqualNode, ArithmeticNode,\
                   NotNode, IsVoidNode, ComplementNode, FunctionCallNode, MemberCallNode, NewNode,\
                   IntegerNode, IdNode, StringNode, BoolNode
from Tools.Semantic import Context, Scope, SelfType, AutoType, SemanticException, ErrorType, Type

# Visitor para inferir los tipos de las variables definidas como Auto_Type.
# Observar que visita los nodos del AST con el scope creado en el Type_Checker.
# LLegado este punto no deben existir inconsistencias semanticas.
# El metodo set_type a una variable se usa para decirle a la variable que su tipo
# debe ser consistente con el tipo que se le pasa por parametro, esto se usa para
# inferir el tipo cuando se requiera.

class Type_Inferer:
    def __init__(self, Context : Context):
        self.Context = Context
        self.Inferences = []
        self.Current_Type = None
        self.Current_method = None

        self.Object_Type = self.Context.get_type('Object')
        self.IO_Type = self.Context.get_type('IO')
        self.String_Type = self.Context.get_type('String')
        self.Int_Type = self.Context.get_type('Int')
        self.Bool_Type = self.Context.get_type('Bool')

    @visitor.on('node')
    def visit(self, node, scope):
        pass

    @visitor.when(ProgramNode)
    def visit(self, node : ProgramNode, scope : Scope):
        for item, child in zip(node.declarations, scope.childs):
            self.visit(item, child)

    @visitor.when(ClassDeclarationNode)
    def visit(self, node : ClassDeclarationNode, scope : Scope):
        self.Current_Type = self.Context.get_type(node.id.lex)

        for feat, child in zip(node.features, scope.childs):
            self.visit(feat, child)

        # Infiere los atributos de la clase que lo necesiten
        for att, var in zip(self.Current_Type.attributes, scope.locals):
            if var.infer_type():
                att.type = var.type
                self.Inferences.append(f'Infered attribute type on line {node.line}, column {node.column}: '
                                       f'On class {self.Current_Type.name}, attribute {att.name}: {var.type.name}.')

    @visitor.when(AttrDeclarationNode)
    def visit(self, node : AttrDeclarationNode, scope : Scope):
        if node.expression:
            att = self.Current_Type.get_attribute(node.id.lex)
            self.visit(node.expression, scope.childs[0], att.type)

            expr_type = node.expression.static_type

            var = scope.childs[0].find_variable(att.name)
            var.set_type(expr_type)

            # Infiere el tipo del atributo si es necesario
            if var.infer_type():
                att.type = var.type
                self.Inferences.append(f'Infered attribute type on line {node.line}, column {node.column}: '
                                       f'On class {self.Current_Type.name}, attribute {att.name}: {var.type.name}.')

    @visitor.when(FuncDeclarationNode)
    def visit(self, node : FuncDeclarationNode, scope : Scope):
        self.Current_method = self.Current_Type.get_method(node.id.lex)
        return_type = self.Current_method.return_type

        self.visit(node.body, scope.childs[0], self.Current_Type if isinstance(return_type, SelfType) else return_type)
        for i, var in enumerate(scope.locals[1:]):
            if var.infer_type():
                # Infiere el tipo del parametro si es necesario
                self.Current_method.param_types[i] = var.type
                self.Inferences.append(f'Infered parameter type on line {node.line}, column {node.column}: '
                                       f'On method {self.Current_method.name}, parameter {var.name}: {var.type.name}.')

        body_type = node.body.static_type
        var = self.Current_method.return_info
        var.set_type(body_type)

        if var.infer_type():
            # Infiere el tipo de retorno del metodo si es necesario
            self.Current_method.return_type = var.type
            self.Inferences.append(f'Infered return type on line {node.line}, column {node.column}: '
                                   f'On method {self.Current_method.name}, return type: {var.type.name}.')

    @visitor.when(IfThenElseNode)
    def visit(self, node : IfThenElseNode, scope : Scope, expected_type : Type = None):
        self.visit(node.condition, scope.childs[0], self.Bool_Type)
        self.visit(node.if_body, scope.childs[1], expected_type)
        self.visit(node.else_body, scope.childs[2], expected_type)

        node.static_type = node.if_body.static_type.type_union(node.else_body.static_type)

    @visitor.when(WhileLoopNode)
    def visit(self, node : WhileLoopNode, scope : Scope, expected_type : Type = None):
        self.visit(node.condition, scope.childs[0], self.Bool_Type)
        self.visit(node.body, scope.childs[1], expected_type)
        node.static_type = node.body.static_type

    @visitor.when(BlockNode)
    def visit(self, node : BlockNode, scope : Scope, expected_type : Type = None):
        for expr, child in zip(node.expressions, scope.childs):
            self.visit(expr, child)
        node.static_type = node.expressions[-1].static_type

    @visitor.when(LetInNode)
    def visit(self, node : LetInNode, scope : Scope, expected_type : Type = None):
        for (id, type, expr), var, child in zip(node.let_body, scope.locals, scope.childs[:-1]):
            if expr:
                self.visit(expr, child)
                var.set_type(expr.static_type)

        self.visit(node.in_body, scope.childs[-1])
        for (id, type, expr), var in zip(node.let_body, scope.locals):
            if var.infer_type():
                # Infiere el tipo de la variable del let si es necesario
                type = var.type
                self.Inferences.append(f'Infered variable type on line {node.line}, column {node.column}: '
                                       f'Variable {id.lex}: {var.type.name}.')
        node.static_type = node.in_body.static_type

    @visitor.when(CaseOfNode)
    def visit(self, node : CaseOfNode, scope : Scope, expected_type : Type = None):
        self.visit(node.expression, scope.childs[0])

        node.static_type = None
        for (id, type, expr), child in zip(node.branches, scope.childs[1:]):
            self.visit(expr, child)
            node.static_type = node.static_type.type_union(expr.static_type) if node.static_type else expr.static_type

    @visitor.when(AssignNode)
    def visit(self, node : AssignNode, scope : Scope, expected_type : Type = None):
        var = scope.find_variable(node.id.lex) if scope.is_defined(node.id.lex) else None
        self.visit(node.expression, scope.childs[0], var.type)

        var.set_type(node.expression.static_type)
        node.static_type = node.expression.static_type

    @visitor.when(NotNode)
    def visit(self, node : NotNode, scope : Scope, expected_type : Type = None):
        self.visit(node.expression, scope.childs[0], self.Bool_Type)
        node.static_type = self.Bool_Type

    @visitor.when(LessEqualNode)
    def visit(self, node : LessEqualNode, scope : Scope, expected_type : Type = None):
        self.visit(node.left, scope.childs[0], self.Int_Type)
        self.visit(node.right, scope.childs[0], self.Int_Type)

        self.static_type = self.Bool_Type

    @visitor.when(LessNode)
    def visit(self, node: LessNode, scope: Scope, expected_type: Type = None):
        self.visit(node.left, scope.childs[0], self.Int_Type)
        self.visit(node.right, scope.childs[0], self.Int_Type)

        self.static_type = self.Bool_Type

    @visitor.when(EqualNode)
    def visit(self, node: EqualNode, scope: Scope, expected_type: Type = None):
        self.visit(node.left, scope.childs[0], node.right.static_type)
        self.visit(node.right, scope.childs[0], node.left.static_type)

        self.static_type = self.Bool_Type

    @visitor.when(ArithmeticNode)
    def visit(self, node : ArithmeticNode, scope : Scope, expected_type : Type = None):
        self.visit(node.left, scope.childs[0], self.Int_Type)
        self.visit(node.right, scope.childs[1], self.Int_Type)

        node.static_type = self.Int_Type

    @visitor.when(IsVoidNode)
    def visit(self, node : IsVoidNode, scope : Scope, expected_type : Type = None):
        self.visit(node.expression, scope.childs[0])
        node.static_type = self.Bool_Type

    @visitor.when(ComplementNode)
    def visit(self, node : ComplementNode, scope : Scope, expected_type : Type = None):
        self.visit(node.expression, scope.childs[0], self.Int_Type)
        node.static_type = self.Int_Type

    @visitor.when(FunctionCallNode)
    def visit(self, node : FunctionCallNode, scope : Scope, expected_type : Type = None):
        node_type = None
        if node.type:
            try:
                node_type = self.Context.get_type(node.type.lex)
            except SemanticException:
                node_type = ErrorType()

            if isinstance(node_type, SelfType) or isinstance(node_type, AutoType):
                node_type = ErrorType()

        self.visit(node.obj, scope.childs[0], node_type)
        obj_type = node.obj.static_type

        try:
            node_type = node_type if node_type else obj_type
            obj_method = node_type.get_method(node.id.lex)
        except SemanticException:
            obj_method = None
            node_type = ErrorType()

        if obj_method and len(obj_method.param_types) == len(node.args):
            for arg, var, child in zip(node.args, obj_method.param_infos, scope.childs[1:]):
                self.visit(arg, child, var.type if var.infered else None)
        else:
            for arg, child in zip(node.args, scope.childs[1:]):
                self.visit(arg, child)

        node.static_type = node_type

    @visitor.when(MemberCallNode)
    def visit(self, node : MemberCallNode, scope : Scope, expected_type : Type = None):
        try:
            obj_method = self.Current_Type.get_method(node.id.lex)
            node_type = self.Current_Type if isinstance(obj_method.return_type, SelfType) else obj_method.return_type
        except SemanticException:
            obj_method = None
            node_type = ErrorType()

        if obj_method and len(obj_method.param_types) == len(node.args):
            for arg, var, child in zip(node.args, obj_method.param_infos, scope.childs):
                self.visit(arg, child, var.type if var.infered else None)
        else:
            for arg, child in zip(node.args, scope.childs[1:]):
                self.visit(arg, child)

        node.static_type = node_type

    @visitor.when(NewNode)
    def visit(self, node : NewNode, scope : Scope, expected_type : Type = None):
        try:
            node_type = self.Context.get_type(node.type.lex)
        except SemanticException:
            node_type = ErrorType()

        node.static_type = node_type

    @visitor.when(IntegerNode)
    def visit(self, node: IntegerNode, scope: Scope, expected_type : Type = None):
        node.static_type = self.Int_Type

    @visitor.when(StringNode)
    def visit(self, node: StringNode, scope: Scope, expected_type : Type = None):
        node.static_type = self.String_Type

    @visitor.when(BoolNode)
    def visit(self, node: BoolNode, scope: Scope, expected_type : Type = None):
        node.static_type = self.Bool_Type

    @visitor.when(IdNode)
    def visit(self, node : IdNode, scope : Scope, expected_type : Type = None):
        if scope.is_defined(node.token.lex):
            var  = scope.find_variable(node.token.lex)

            if expected_type:
                var.set_type(expected_type)

            node.static_type = var.type if var.infered else AutoType()
        else:
            node.static_type = ErrorType()




