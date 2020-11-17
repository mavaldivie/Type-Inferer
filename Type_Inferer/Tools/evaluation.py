from Tools.parsing import ShiftReduceParser

'''
Este metodo retorna el ast dado el conjunto de producciones,
las operaciones y los tokens
'''
def evaluate_reverse_parse(right_parse, operations, tokens):
    if not right_parse or not operations or not tokens:
        return

    right_parse = iter(right_parse)
    tokens = iter(tokens)
    stack = []
    for operation in operations:
        # Si hay que hacer un shift, pasemos a analizar
        # el proximo token e incluyamoslo en la pila
        if operation == ShiftReduceParser.SHIFT:
            token = next(tokens)
            stack.append(token)
        # Si hay que hacer un reduce, tomamos los elementos
        # necesarios de la pila y los sustituimos por el nonterminal
        # correspondiente, el cual incluimos en la pila
        elif operation == ShiftReduceParser.REDUCE:
            production = next(right_parse)
            head, body = production
            attributes = production.attributes
            assert all(rule is None for rule in attributes[1:]), 'There must be only syntheticed attributes.'
            rule = attributes[0]

            if len(body):
                syntheticed = [None] + stack[-len(body):]
                value = rule(None, syntheticed)
                stack[-len(body):] = [value]
            else:
                stack.append(rule(None, None))
        else:
            raise Exception('Invalid action!!!')

    # La pila debe terminar con el program node
    # correspondiente a la raiz del ast, todos los
    # tokens deben haber sido analizados
    assert len(stack) == 1
    assert next(tokens).token_type == '$'#######estaba EOF, creo que tiene que ver con lo que cambie al poner el tokentype en el lexer
    return stack[0]