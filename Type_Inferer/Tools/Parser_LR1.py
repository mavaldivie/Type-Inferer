from Tools.pycompiler import Item
from Tools.utils import ContainerSet
from Tools.Firsts_and_Follows import compute_firsts, compute_local_first
from Tools.automata import State
from Tools.parsing import ShiftReduceParser

'''
Recibe un item LR(1) y devuelve el conjunto de items que 
sugiere incluir (directamente) debido a la presencia de 
un . delante de un no terminal.
expand("𝑌→𝛼.𝑋𝛿,𝑐") = { "𝑋→.𝛽,𝑏" | 𝑏∈𝐹𝑖𝑟𝑠𝑡(𝛿𝑐) }
'''
def expand(item, firsts):
    next_symbol = item.NextSymbol
    if next_symbol is None or not next_symbol.IsNonTerminal:
        return []

    lookaheads = ContainerSet()
    # (Compute lookahead for child items)
    # Preview retorna los elementos que se encuantran detras del punto
    # en el item mas sus lookaheads
    for prev in item.Preview():
        lookaheads.update(compute_local_first(firsts, prev))

    assert not lookaheads.contains_epsilon

    # (Build and return child items)
    return [Item(x, 0, lookaheads) for x in next_symbol.productions]

'''
Recibe un conjunto de items LR(1) y devuelve el mismo conjunto pero
en el que los items con mismo centro están unidos (se combinan los lookahead).
'''
def compress(items):
    centers = {}

    for item in items:
        center = item.Center()
        try:
            lookaheads = centers[center]
        except KeyError:
            centers[center] = lookaheads = set()
        lookaheads.update(item.lookaheads)

    return {Item(x.production, x.pos, set(lookahead)) for x, lookahead in centers.items()}

'''
Computa la clausura de un conjunto de items
'''
# Metodo de punto fijo, mientras haya cambios en el conjunto de items,
# itero por todos los items X -> v.Yw,p, donde X y Y son noterminales y
# v y w son formas oracionales, e incluyo los items de la forma
# Y -> Z,b donde b ∈ First(wp), para todas las producciones de Y.
# Dischos items se calculan mediantes el metodo expand.
# 𝐶𝐿(𝐼) = 𝐼 ∪ { 𝑋→.𝛽,𝑏 }
# tales que 𝑌→𝛼.𝑋𝛿,𝑐 ∈ 𝐶𝐿(𝐼) y 𝑏 ∈ 𝐹𝑖𝑟𝑠𝑡(𝛿𝑐)

def closure_lr1(items, firsts):
    closure = ContainerSet(*items)

    changed = True
    while changed:
        changed = False

        new_items = ContainerSet()
        for item in closure:
            new_items.extend(expand(item, firsts))

        changed = closure.update(new_items)

    return compress(closure)

'''
Recibe como parámetro un conjunto de items y un símbolo, y devuelve el
conjunto goto(items, symbol). El método permite setear el parámentro 
just_kernel=True para calcular solamente el conjunto de items kernels 
en lugar de todo el conjunto de items. En caso contrario, se debe proveer 
el conjunto con los firsts de la gramática, puesto que serán usados al 
calcular la clausura.
'''
# 𝐺𝑜𝑡𝑜(𝐼,𝑋) = 𝐶𝐿({ 𝑌→𝛼𝑋.𝛽,𝑐 | 𝑌→𝛼.𝑋𝛽,𝑐 ∈ 𝐼})
def goto_lr1(items, symbol, firsts=None, just_kernel=False):
    assert just_kernel or firsts is not None, '`firsts` must be provided if `just_kernel=False`'
    items = frozenset(item.NextItem() for item in items if item.NextSymbol == symbol)
    return items if just_kernel else closure_lr1(items, firsts)

'''
Computa el automata LR1 correspondiente a la gramatica
'''
# El estado inicial es la clausura del item S' -> .S, $.
# Todos los estados son finales.
# Las transiciones ocurren con terminales y no terminales.
# La función de transición está dada por la función goto.
#    f(Ii, c) = Goto(Ii, c)
def build_LR1_automaton(G):
    assert len(G.startSymbol.productions) == 1, 'Grammar must be augmented'

    firsts = compute_firsts(G)
    firsts[G.EOF] = ContainerSet(G.EOF)

    start_production = G.startSymbol.productions[0]
    start_item = Item(start_production, 0, lookaheads=(G.EOF,))
    start = frozenset([start_item])

    # El estado inicial es la clausura del item S' -> .S, $
    closure = closure_lr1(start, firsts)
    automaton = State(frozenset(closure), True)

    pending = [start]
    visited = {start: automaton}

    # BFS para construir el automata
    # Mientras hallan estados pendientes
    while pending:
        # Tomo el siguiente estado a analizar
        current = pending.pop()
        current_state = visited[current]

        # Itero por cada simbolo de la gramatica
        for symbol in G.terminals + G.nonTerminals:
            # Chequeo si el estado actual posee transicion con ese simbolo a algun estado x
            next_state_key = goto_lr1(current_state.state, symbol, just_kernel=True)

            # Si no la posee, continuo al siguiente simbolo
            if not next_state_key:
                continue
            try:
                next_state = visited[next_state_key]
            except KeyError:
                # Si el estado x no ha sido visto por el bfs, lo incluyo
                # en la lista de pending
                next_state_items = goto_lr1(current_state.state, symbol, firsts)
                next_state = State(frozenset(next_state_items), True)
                pending.append(next_state_key)
                visited[next_state_key] = next_state

            # incluto la transicion del estado actual a x con el simbolo actual
            current_state.add_transition(symbol.Name, next_state)

    #automaton.set_formatter(multiline_formatter)
    return automaton


# Recordar que la diferencia entre los parsers Shift-Reduce es solo la forma
# en que se llenan las tablas ACTION y GOTO
class LR1Parser(ShiftReduceParser):
    def _build_parsing_table(self):
        G = self.G.AugmentedGrammar(True)

        automaton = build_LR1_automaton(G)
        for i, node in enumerate(automaton):
            node.idx = i

        for node in automaton:
            idx = node.idx
            for item in node.state:
                # - Fill `self.Action` and `self.Goto` according to `item`)
                # - Feel free to use `self._register(...)`)
                if item.IsReduceItem:
                    if item.production.Left == G.startSymbol:
                        # Sea 𝐼𝑖 el estado que contiene el item "𝑆′→𝑆.,$" (𝑆′ distinguido).
                        # Entonces 𝐴𝐶𝑇𝐼𝑂𝑁[𝐼𝑖,$]=‘𝑂𝐾‘
                        self._register(self.action, (idx, G.EOF.Name), (self.OK, None))
                    else:
                        # Sea "𝑋→𝛼.,𝑠" un item del estado 𝐼𝑖.
                        # Entonces 𝐴𝐶𝑇𝐼𝑂𝑁[𝐼𝑖,𝑠]=‘𝑅𝑘‘ (producción k es 𝑋→𝛼)
                        for c in item.lookaheads:
                            self._register(self.action, (idx, c.Name), (self.REDUCE, item.production))
                else:
                    next_symbol = item.NextSymbol
                    try:
                        next_state = node[next_symbol.Name][0]
                        if next_symbol.IsNonTerminal:
                            # Sea "𝑋→𝛼.𝑌𝜔,𝑠" item del estado 𝐼𝑖 y 𝐺𝑜𝑡𝑜(𝐼𝑖,𝑌)=𝐼𝑗.
                            # Entonces 𝐺𝑂𝑇𝑂[𝐼𝑖,𝑌]=𝑗
                            self._register(self.goto, (idx, next_symbol.Name), next_state.idx)
                        else:
                            # Sea "𝑋→𝛼.𝑐𝜔,𝑠" un item del estado 𝐼𝑖 y 𝐺𝑜𝑡𝑜(𝐼𝑖,𝑐)=𝐼𝑗.
                            # Entonces 𝐴𝐶𝑇𝐼𝑂𝑁[𝐼𝑖,𝑐]=‘𝑆𝑗‘
                            self._register(self.action, (idx, next_symbol.Name), (self.SHIFT, next_state.idx))
                    except KeyError:
                        print(f'Node: {node} without transition with symbol {next_symbol}')
                        return


