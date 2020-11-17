import ply.lex as lex
from Tools.utils import Token
from Parser import CoolGrammar

#Tokenizer

tokens_dict = {}
# Simbolos del lenguaje COOL
literals = ['+', '-', '*', '/', ':', ';', '(', ')', '{', '}', '@', '.', ',']

# Palabras reservadas del lenguaje COOL
reserved = {
    'class': 'CLASS',
    'inherits': 'INHERITS',
    'function': 'FUNCTION',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'fi': 'FI',
    'while': 'WHILE',
    'loop': 'LOOP',
    'pool': 'POOL',
    'let': 'LET',
    'in': 'IN',
    'case': 'CASE',
    'of': 'OF',
    'esac': 'ESAC',
    'new': 'NEW',
    'isvoid': 'ISVOID'
}

ignored = [' ', '\n', '\f', '\r', '\t', '\v']

tokens = [
             # Identifiers
             'TYPE', 'ID',
             # Primitive data types
             'INTEGER', 'STRING', 'BOOL',
             # Special keywords
             'ACTION',
             # Operators
             'ASSIGN', 'LESS', 'LESSEQUAL', 'EQUAL', 'INT_COMPLEMENT', 'NOT',
         ] + list(reserved.values())

for tok in tokens + literals:
    try:
        tokens_dict[tok] = CoolGrammar[tok.lower()]
    except KeyError:
        pass

tokens_dict['ACTION'] = CoolGrammar['=>']
tokens_dict['ASSIGN'] = CoolGrammar['<-']
tokens_dict['LESS'] = CoolGrammar['<']
tokens_dict['LESSEQUAL'] = CoolGrammar['<=']
tokens_dict['EQUAL'] = CoolGrammar['=']
tokens_dict['INT_COMPLEMENT'] = CoolGrammar['~']


# Expresiones regulares

def t_INTEGER(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


def t_STRING(t):
    r'"(\\"|[^\0\n"])*(\\\n[^\0\n"]*)*"'
    t.value = t.value[1:-1]
    return t


def t_BOOL(t):
    r'true|false'
    t.value = True if t.value == 'true' else False
    return t


def t_COMMENT(t):
    r'--[^\n]+\n|\(\*[^(\*\))]+\*\)'
    pass


# Other tokens with precedence before TYPE and ID

def t_NOT(t):
    r'[nN][oO][tT]'
    return t


# Identifiers

def t_TYPE(t):
    r'[A-Z][A-Za-z0-9_]*'
    return t


def t_ID(t):
    r'[a-z][A-Za-z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    return t


t_ASSIGN = r'<-'
t_LESS = r'<'
t_LESSEQUAL = r'<='
t_EQUAL = r'='
t_INT_COMPLEMENT = r'~'

# Special keywords

t_ACTION = r'=>'


###### SPECIAL RULES ######

def t_error(t):
    print("Illegal character '{}'".format(t.value[0]))
    t.lexer.skip(1)


t_ignore = ''.join(ignored)

###### CREATE LEXER ######
# Usa ply
lex.lex()


'''
Dado un string retorna el arreglo de tokens resultante de analizar dicho string
'''
def tokenizer(code):
    tokens = []

    for i, line in enumerate(code.split('\n')):
        lex.input(line)
        while True:
            token = lex.token()
            if token is None:
                break
            tokens.append(Token(token.value, tokens_dict[token.type].Name, i + 1, token.lexpos))

    tokens.append(Token('$', CoolGrammar.EOF.Name))

    return tokens
