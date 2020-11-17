from Lexer import tokenizer
from Parser import CoolParser
from Tools.evaluation import evaluate_reverse_parse
from format_visitor import FormatVisitor
from Type_Collector import Type_Collector
from Type_Builder import Type_Builder
from Type_Checker import Type_Checker
from Type_Inferer import Type_Inferer

# Esta es la clase que maneja el proceso de inferencia de tipos

'''
    Recibe un string con el codigo del programa COOL y devuelve 
    el resultado de analizar dicho string
'''
class Type_Inferer_Controller:
    def __call__(self, program_code: str):
        ret = ['Tokenizing... Done\n']
        tokens = tokenizer(program_code)
        ret[-1] += 'Tokens = ' \
               '{\n\t' + \
                    '\n\t'.join(f'(lex: {i.lex}, type: {i.token_type})' for i in tokens) + \
               '\n}\n\n'

        ret += ['Parsing... Done\n']
        errors = []
        productions, operations = CoolParser(tokens, errors)
        if errors:
            ret[-1] += 'There have been errors while parsing:\n' + \
                    '\n'.join(str(i) for i in errors)
            return ret
        ret[-1] += 'Productions:\n' + \
               '\n'.join(str(i) for i in productions) + '\n\n'

        ret += ['Building Abstract Syntax Tree... Done']
        ast = evaluate_reverse_parse(productions, operations, tokens)

        formatter = FormatVisitor()
        tree = formatter.visit(ast)
        ret[-1] += f'\n{tree}'

        ret += ['Collecting types... Done\n']
        collector = Type_Collector()
        collector.visit(ast)
        if collector.Errors:
            ret[-1] += 'There have been errors while collecting types:\n' + \
                   '\n'.join(i for i in collector.Errors)
            return ret

        ret += ['Building Types... Done\n']
        builder = Type_Builder(collector.Context)
        builder.visit(ast)
        if builder.Errors:
            ret[-1] += 'There have been errors while building types:\n' + \
                   '\n'.join(i for i in builder.Errors)
            return ret
        ret[-1] += f'Types:\n{builder.Context}\n\n'

        ret += ['Checking types... Done\n']
        checker = Type_Checker(builder.Context)
        scope = checker.visit(ast)
        if checker.Errors:
            ret[-1] += 'There have been errors while checking types:\n' + \
                   '\n'.join(i for i in checker.Errors)
            return ret
        else:
            ret[-1] += '\n'

        ret += ['Infering types... Done\n']
        inferer = Type_Inferer(checker.Context)
        inferer.visit(ast, scope)
        if inferer.Inferences:
            ret[-1] += 'Inferences:\n' + \
                   '\n'.join(i for i in inferer.Inferences)
        else:
            ret[-1] += 'No inferences have been done.'

        return ret