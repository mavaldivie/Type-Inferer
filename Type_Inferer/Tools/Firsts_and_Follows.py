from Tools.utils import ContainerSet

'''
Dada una forma oracional alpha computa sus firsts
'''
def compute_local_first(firsts, alpha):
    first_alpha = ContainerSet()

    try:
        alpha_is_epsilon = alpha.IsEpsilon
    except:
        alpha_is_epsilon = False

    # alpha == epsilon ? First(alpha) = { epsilon }
    if alpha_is_epsilon:
        first_alpha.set_epsilon()
        return first_alpha

    # alpha = X1 ... XN
    # First(Xi) subconjunto First(alpha)
    # epsilon pertenece a First(X1)...First(Xi) ? First(Xi+1) subconjunto de First(X) y First(alpha)
    # epsilon pertenece a First(X1)...First(XN) ? epsilon pertence a First(X) y al First(alpha)
    for symbol in alpha:
        first_alpha.update(firsts[symbol])
        if not firsts[symbol].contains_epsilon:
            break
    else:
        first_alpha.set_epsilon()

    return first_alpha


'''
Computa los firsts de todos los simbolos de la gramatica
'''
def compute_firsts(G):
    firsts = {}
    change = True

    # Los firsts de los terminales son ellos mismos
    for terminal in G.terminals:
        firsts[terminal] = ContainerSet(terminal)

    # Inicializa los firsts de los noterminales como un conjunto vacio
    for nonterminal in G.nonTerminals:
        firsts[nonterminal] = ContainerSet()

    # Metodo de punto fijo, mientras halla algun cambio en los firsts
    # de algun simbolo, itera por todas las producciones recalculando los firsts
    # del noterminal correspondiente
    while change:
        change = False

        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right

            # get current First(X)
            first_X = firsts[X]

            # init First(alpha)
            try:
                first_alpha = firsts[alpha]
            except KeyError:
                first_alpha = firsts[alpha] = ContainerSet()

            # CurrentFirst(alpha)
            local_first = compute_local_first(firsts, alpha)

            # update First(X) and First(alpha) from CurrentFirst(alpha)
            change |= first_alpha.hard_update(local_first)
            change |= first_X.hard_update(local_first)

    return firsts

'''
Computa los follows de cada noterminal de la gramatica
'''
from itertools import islice
def compute_follows(G, firsts):
    follows = {}
    change = True

    local_firsts = {}

    # Inicializa los follows de los noterminales como un conjunto vacio
    for nonterminal in G.nonTerminals:
        follows[nonterminal] = ContainerSet()
    # EOF pertenece a los follows del simbolo inicial
    follows[G.startSymbol] = ContainerSet(G.EOF)

    # Metodo de punto fijo, mientras haya cambios en los follows
    # de algun noterminal, itera por todas las producciones y recalcula
    # los follows de cada noterminal
    while change:
        change = False

        # P: X -> alpha
        for production in G.Productions:
            X = production.Left
            alpha = production.Right

            follow_X = follows[X]

            # Si la produccion actual es de la forma X -> v Y w
            # donde v y w son formas oracionales entonces cada elemento
            # que pertenece al first de w (excepto epsilon) pertenece tambien al follow
            # de Y. Si ademas w ->* epsilon entonces los follows de X pertenecen
            # al follows de Y.
            # X -> zeta Y beta
            # First(beta) - { epsilon } subset of Follow(Y)
            # beta ->* epsilon or X -> zeta Y ? Follow(X) subset of Follow(Y)
            for i, symbol in enumerate(alpha):
                if symbol.IsNonTerminal:
                    try:
                        first_beta = local_firsts[alpha, i]
                    except KeyError:
                        first_beta = local_firsts[alpha, i] = compute_local_first(firsts, islice(alpha, i + 1, None))

                    change |= follows[symbol].update(first_beta)

                    if first_beta.contains_epsilon:
                        change |= follows[symbol].update(follow_X)

    return follows


