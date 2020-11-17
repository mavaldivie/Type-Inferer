from Tools.Errors import *

# Clase base para los parsers Shift-Reduce
class ShiftReduceParser:
    SHIFT = 'SHIFT'
    REDUCE = 'REDUCE'
    OK = 'OK'

    def __init__(self, G, verbose=False):
        self.G = G
        self.verbose = verbose
        self.action = {}
        self.goto = {}
        self.HasConflict = False
        self._build_parsing_table()

    def _build_parsing_table(self):
        raise NotImplementedError()

    '''
    Retorna las producciones y operaciones necesarias para el
    proceso de parsing del string w.
    '''
    def __call__(self, w, errors = None):
        stack = [0]
        cursor = 0
        output = []
        operations = []

        while True:
            # Estado del automata en el que me encuentro
            state = stack[-1]
            # Siguiente simbolo a analizar
            lookahead = w[cursor].token_type
            if self.verbose: print(stack, '<---||--->', w[cursor:])
            #(Detect error)
            try:
                action, tag = self.action[state, lookahead][0]
            except KeyError:
                # Si no existe transicion desde el estado actual con el simbolo
                # correspondiente es porque ha habido un error
                lookahead = w[cursor]
                line = lookahead.line
                column = lookahead.column
                if lookahead.lex == '$':
                    errors.append(UnexpectedError(line, column, 'EOF'))
                else:
                    errors.append(UnresolvedReferenceError(line, column, lookahead.lex))
                return None, None

            # Si la accion es Shift, incluyo en la pila el simbolo actual y
            # el estado al que necesito moverme
            if action == self.SHIFT:
                stack.append(lookahead)
                stack.append(tag)
                operations.append(self.SHIFT)
                cursor += 1
            # Si la accion es Reduce, saco de la pila los simbolos correspondientes
            # a la produccion q debo reducir
            elif action == self.REDUCE:
                output.append(tag)
                for i in range(len(tag.Right)):
                    stack.pop()
                    assert stack[-1] == tag.Right[-i - 1].Name, 'Symbol does not match'
                    stack.pop()
                # Tomo el estado al que debo moverme
                index = self.goto[stack[-1], tag.Left.Name][0]
                # Incluyo en la pila el simbolo reducido y el estado al
                # que necesito moverme
                stack.append(tag.Left.Name)
                stack.append(index)
                operations.append(self.REDUCE)
            #(OK case)
            elif action == self.OK:
                return output, operations
            #(Invalid case)
            else:
                lookahead = w[cursor]
                line = lookahead.line
                column = lookahead.column
                if lookahead.lex == '$':
                    errors.append(UnexpectedError(line, column, 'EOF'))
                else:
                    errors.append(UnresolvedReferenceError(line, column, lookahead.lex))
                return None, None

    def action_goto_tables(self):
        return  table_to_dataframe(self.action), table_to_dataframe(self.goto)
    def _register(self, table, key, value):
        if key not in table:
            table[key] = [value]
        elif not any(i for i in table[key] if i == value):
            self.HasConflict = True
            table[key].append(value)


from pandas import DataFrame
def encode_value(value):
    try:
        action, tag = value[0]
        if action == ShiftReduceParser.SHIFT:
            return 'S' + str(tag)
        elif action == ShiftReduceParser.REDUCE:
            return repr(tag)
        elif action ==  ShiftReduceParser.OK:
            return action
        else:
            return value
    except ValueError:
        return value[0]
    except TypeError:
        return value[0]

def table_to_dataframe(table):
    d = {}
    for (state, symbol), value in table.items():
        value = encode_value(value)
        try:
            d[state][symbol] = value
        except KeyError:
            d[state] = { symbol: value }

    return DataFrame.from_dict(d, orient='index', dtype=str)