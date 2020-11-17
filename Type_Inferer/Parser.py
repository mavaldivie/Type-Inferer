from Tools.pycompiler import Grammar
from Tools.Parser_LR1 import LR1Parser


# Clases necesarias para representar el AST del programa COOL
class Node:
    pass

# Raiz del AST
class ProgramNode(Node):
    def __init__(self, declarations):
        self.declarations = declarations
        self.line = declarations[0].line
        self.column = declarations[0].column


class DeclarationNode(Node):
    pass


class ClassDeclarationNode(DeclarationNode):
    def __init__(self, idx, features, parent=None):
        self.id = idx
        self.parent = parent
        self.features = features
        self.line = idx.line
        self.column = idx.column


class AttrDeclarationNode(DeclarationNode):
    def __init__(self, idx, typex, expression=None):
        self.id = idx
        self.type = typex
        self.expression = expression
        self.line = idx.line
        self.column = idx.column


class FuncDeclarationNode(DeclarationNode):
    def __init__(self, idx, params, return_type, body):
        self.id = idx
        self.params = params
        self.type = return_type
        self.body = body
        self.line = idx.line
        self.column = idx.column


class ExpressionNode(Node):
    pass


class IfThenElseNode(ExpressionNode):
    def __init__(self, condition, if_body, else_body):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        self.line = condition.line
        self.column = condition.column


class WhileLoopNode(ExpressionNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        self.line = condition.line
        self.column = condition.column


class BlockNode(ExpressionNode):
    def __init__(self, expressions):
        self.expressions = expressions
        self.line = expressions[-1].line
        self.column = expressions[-1].column


class LetInNode(ExpressionNode):
    def __init__(self, let_body, in_body):
        self.let_body = let_body
        self.in_body = in_body
        self.line = in_body.line
        self.column = in_body.column


class CaseOfNode(ExpressionNode):
    def __init__(self, expression, branches):
        self.expression = expression
        self.branches = branches
        self.line = expression.line
        self.column = expression.column


class AssignNode(ExpressionNode):
    def __init__(self, idx, expression):
        self.id = idx
        self.expression = expression
        self.line = idx.line
        self.column = idx.column


class UnaryNode(ExpressionNode):
    def __init__(self, expression):
        self.expression = expression
        self.line = expression.line
        self.column = expression.column


class NotNode(UnaryNode):
    pass


class BinaryNode(ExpressionNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.line = left.line
        self.column = left.column


class LessEqualNode(BinaryNode):
    pass


class LessNode(BinaryNode):
    pass


class EqualNode(BinaryNode):
    pass


class ArithmeticNode(BinaryNode):
    pass


class PlusNode(ArithmeticNode):
    pass


class MinusNode(ArithmeticNode):
    pass


class StarNode(ArithmeticNode):
    pass


class DivNode(ArithmeticNode):
    pass


class IsVoidNode(UnaryNode):
    pass


class ComplementNode(UnaryNode):
    pass


class FunctionCallNode(ExpressionNode):
    def __init__(self, obj, idx, args, typex=None):
        self.obj = obj
        self.id = idx
        self.args = args
        self.type = typex
        self.line = idx.line
        self.column = idx.column


class MemberCallNode(ExpressionNode):
    def __init__(self, idx, args):
        self.id = idx
        self.args = args
        self.line = idx.line
        self.column = idx.column


class NewNode(ExpressionNode):
    def __init__(self, typex):
        self.type = typex
        self.line = typex.line
        self.column = typex.column


class AtomicNode(ExpressionNode):
    def __init__(self, token):
        self.token = token
        self.line = token.line
        self.column = token.column


class IntegerNode(AtomicNode):
    pass


class IdNode(AtomicNode):
    pass


class StringNode(AtomicNode):
    pass


class BoolNode(AtomicNode):
    pass


# Representacion de la gramatica de COOL utilizando la clase grammar
CoolGrammar = Grammar()

# noterminales
program = CoolGrammar.NonTerminal('<program>', startSymbol=True)
class_list, def_class = CoolGrammar.NonTerminals('<class-list> <def-class>')
feature_list, feature = CoolGrammar.NonTerminals('<feature-list> <feature>')
param_list, param = CoolGrammar.NonTerminals('<param-list> <param>')
expr, member_call, expr_list, let_list, case_list = CoolGrammar.NonTerminals(
    '<expr> <member-call> <expr-list> <let-list> <case-list>')
comp_expr, arith, arith_2, term, factor, factor_2 = CoolGrammar.NonTerminals(
    '<comp-expr> <arith> <arith-2> <term> <factor> <factor-2>')
atom, func_call, arg_list = CoolGrammar.NonTerminals('<atom> <func-call> <arg-list>')

# terminales
classx, inherits, function = CoolGrammar.Terminals('class inherits function')
ifx, then, elsex, fi = CoolGrammar.Terminals('if then else fi')
whilex, loop, pool = CoolGrammar.Terminals('while loop pool')
let, inx = CoolGrammar.Terminals('let in')
case, of, esac = CoolGrammar.Terminals('case of esac')
semi, colon, comma, dot, at, opar, cpar, ocur, ccur, larrow, rarrow = CoolGrammar.Terminals(
    '; : , . @ ( ) { } <- =>')
plus, minus, star, div, isvoid, compl = CoolGrammar.Terminals('+ - * / isvoid ~')
notx, less, leq, equal = CoolGrammar.Terminals('not < <= =')
new, idx, typex, integer, string, boolx = CoolGrammar.Terminals('new id type integer string bool')

# Producciones
program %= class_list, lambda h, s: ProgramNode(s[1])

# Lista de clases
class_list %= def_class + class_list, lambda h, s: [s[1]] + s[2]
class_list %= def_class, lambda h, s: [s[1]]

# Defincicion de la clase
def_class %= classx + typex + ocur + feature_list + ccur + semi, lambda h, s: ClassDeclarationNode(s[2], s[4])
def_class %= classx + typex + inherits + typex + ocur + feature_list + ccur + semi, lambda h, s: ClassDeclarationNode(
    s[2], s[6], s[4])

# Lista de propiedades de la clase
feature_list %= feature + feature_list, lambda h, s: [s[1]] + s[2]
feature_list %= CoolGrammar.Epsilon, lambda h, s: []

# Atributos de la clase
feature %= idx + colon + typex + semi, lambda h, s: AttrDeclarationNode(s[1], s[3])
feature %= idx + colon + typex + larrow + expr + semi, lambda h, s: AttrDeclarationNode(s[1], s[3], s[5])

# Metodos constructores de la clase
feature %= idx + opar + param_list + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclarationNode(
    s[1], s[3], s[6], s[8])
feature %= idx + opar + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclarationNode(s[1], [],
                                                                                                           s[5], s[7])
# Metodos de la clase
feature %= function + idx + opar + param_list + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclarationNode(
    s[2], s[4], s[7], s[9])
feature %= function + idx + opar + cpar + colon + typex + ocur + expr + ccur + semi, lambda h, s: FuncDeclarationNode(s[2], [],
                                                                                                           s[6], s[8])
# Lista de parametros de funcion
param_list %= param, lambda h, s: [s[1]]
param_list %= param + comma + param_list, lambda h, s: [s[1]] + s[3]

# parametro de funcion
param %= idx + colon + typex, lambda h, s: (s[1], s[3])

### Expresiones ###
# Expresion de asignacion
expr %= idx + larrow + expr, lambda h, s: AssignNode(s[1], s[3])

# Se coloca mayor prioridad al let in que el resto de
# expresiones para evitar ambiguedades
# Expresion Let-in
expr %= let + let_list + inx + expr, lambda h, s: LetInNode(s[2], s[4])

# Lista de expresiones del let
let_list %= idx + colon + typex, lambda h, s: [(s[1], s[3], None)]
let_list %= idx + colon + typex + larrow + expr, lambda h, s: [(s[1], s[3], s[5])]
let_list %= idx + colon + typex + comma + let_list, lambda h, s: [(s[1], s[3], None)] + s[5]
let_list %= idx + colon + typex + larrow + expr + comma + let_list, lambda h, s: [(s[1], s[3], s[5])] + s[7]

# Expresion new
expr %= new + typex, lambda h, s: NewNode(s[2])
# Expresion isvoid
expr %= isvoid + expr, lambda h, s: IsVoidNode(s[2])

# Expresiones booleanas de comparacion
expr %= arith + less + arith, lambda h, s: LessNode(s[1], s[3])
expr %= arith + leq + arith, lambda h, s: LessEqualNode(s[1], s[3])
expr %= arith + equal + arith, lambda h, s: EqualNode(s[1], s[3])
expr %= arith, lambda h, s:s[1]

#Expresiones aritmeticas
expr %= arith + plus + arith, lambda h, s: PlusNode(s[1], s[3])
expr %= arith + minus + arith, lambda h, s: MinusNode(s[1], s[3])
arith %= factor + star + factor, lambda h, s: StarNode(s[1], s[3])
arith %= factor + div + factor, lambda h, s: DivNode(s[1], s[3])
arith %= factor, lambda h, s: s[1]

# Expresion de complemento ~
factor %= compl + atom, lambda h, s: ComplementNode(s[2])
# Expresion de negacion not
factor %= notx + atom, lambda h, s: NotNode(s[2])

factor %= atom, lambda h, s: s[1]

# Encapsulaciones atomicas
atom %= opar + expr + cpar, lambda h, s: s[2]
atom %= integer, lambda h, s: IntegerNode(s[1])
atom %= string, lambda h, s: StringNode(s[1])
atom %= boolx, lambda h, s: BoolNode(s[1])
atom %= idx, lambda h, s: IdNode(s[1])
atom %= ifx + expr + then + expr + elsex + expr + fi, lambda h, s: IfThenElseNode(s[2], s[4], s[6])
atom %= whilex + expr + loop + expr + pool, lambda h, s: WhileLoopNode(s[2], s[4])

# Encapsulamiento entre corchetes
atom %= ocur + expr_list + ccur, lambda h, s: BlockNode(s[2])
expr_list %= expr + semi, lambda h, s: [s[1]]
expr_list %= expr + semi + expr_list, lambda h, s: [s[1]] + s[3]

# Expresion Case of
atom %= case + expr + of + case_list + esac, lambda h, s: CaseOfNode(s[2], s[4])
case_list %= idx + colon + typex + rarrow + expr + semi, lambda h, s: [(s[1], s[3], s[5])]
case_list %= idx + colon + typex + rarrow + expr + semi + case_list, lambda h, s: [(s[1], s[3], s[5])] + s[7]

# Llamado a miembro de clase
atom %= idx + opar + arg_list + cpar, lambda h, s: MemberCallNode(s[1], s[3])
atom %= idx + opar + cpar, lambda h, s: MemberCallNode(s[1], [])

# Llamado a funcion
atom %= atom + dot + idx + opar + arg_list + cpar, lambda h, s: FunctionCallNode(s[1], s[3], s[5])
atom %= atom + dot + idx + opar + cpar, lambda h, s: FunctionCallNode(s[1], s[3], [])
atom %= atom + at + typex + dot + idx + opar + arg_list + cpar, lambda h, s: FunctionCallNode(s[1], s[5], s[7], s[3])
atom %= atom + at + typex + dot + idx + opar + cpar, lambda h, s: FunctionCallNode(s[1], s[5], [], s[3])

# Lista de argumentos
arg_list %= expr, lambda h, s: [s[1]]
arg_list %= expr + comma + arg_list, lambda h, s: [s[1]] + s[3]

# parser
CoolParser = LR1Parser(CoolGrammar)
