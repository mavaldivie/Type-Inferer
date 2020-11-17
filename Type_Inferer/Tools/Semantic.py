# Aqui estan las clases necesarias para representar los tipos del programa

# Necesario para enviar errores semanticos
class SemanticException(Exception):
    @property
    def text(self):
        return self.args[0]

# Representa un atributo en un tipo del programa
class Attribute:
    def __init__(self, name : str, type, expression = None):
        self.name = name
        self.type = type

    def __str__(self):
        return f'[attrib] {self.name}: {self.type.name};'

    def __repr__(self):
        return str(self)

# Representa un metodo en un tipo del programa
class Method:
    def __init__(self, name : str, param_names : list, param_types : list, return_type):
        self.name = name
        self.param_names = param_names
        self.param_types = param_types
        self.return_type = return_type
        self.param_infos = [VariableInfo(f'_{name}_{pname}', ptype) for pname, ptype in zip(param_names, param_types)]
        self.return_info = VariableInfo(f'_{name}', return_type)

    def __str__(self):
        params = ', '.join(f'{n}: {t.name}' for n, t in zip(self.param_names, self.param_types))
        return f'[method] {self.name}({params}): {self.return_type.name};'

    def __eq__(self, other):
        return other.name == self.name and \
               other.return_type == self.return_type and \
               other.param_types == self.param_types

#Clase base para representar los tipos del programa
class Type:
    def __init__(self, name:str, sealed=False):
        self.name = name
        self.attributes = []
        self.methods = {}
        self.parent = None
        # Profundidad en el arbol de herencia
        self.depth = 0
        # True si la clase esta sellada (no se puede heredar de ella)
        self.sealed = sealed

    def set_parent(self, parent):
        # Si el padre esta definido o es un tipo sellado entonces hay un error semantico
        if self.parent is not None:
            raise SemanticException(f'Parent type is already set for {self.name}.')
        if parent.sealed:
            raise SemanticException(f'Parent type "{parent.name}" is sealed. Can\'t inherit from it.')
        self.parent = parent
        self.depth = parent.depth + 1

    # Retorna el tipo en el arbol de herencia de mayor profundidad
    # que es padre comun de ambos tipos
    def type_union(self, other):
        x, y = self, other
        while x.depth > y.depth:
            x = x.parent
        while y.depth > x.depth:
            y = y.parent

        while x and x != y:
            x = x.parent
            y = y.parent

        return x

    # Retorna el atributo del tipo actual con el nombre correspondiente
    def get_attribute(self, name:str):
        try:
            return next(attr for attr in self.attributes if attr.name == name)
        except StopIteration:
            if self.parent is None:
                raise SemanticException(f'Attribute "{name}" is not defined in {self.name}.')
            try:
                return self.parent.get_attribute(name)
            except SemanticException:
                raise SemanticException(f'Attribute "{name}" is not defined in {self.name}.')

    # Define un atributo para el tipo actual con el nombre y el tipo correspondiente
    def define_attribute(self, name:str, typex):
        try:
            self.get_attribute(name)
        except SemanticException:
            attribute = Attribute(name, typex)
            self.attributes.append(attribute)
            return attribute
        else:
            raise SemanticException(f'Attribute "{name}" is already defined in {self.name}.')

    # Retporna el metodo del tipo actual con el nombre correspondiente
    def get_method(self, name:str):
        try:
            return self.methods[name]
        except KeyError:
            if self.parent is None:
                raise SemanticException(f'Method "{name}" is not defined in {self.name}.')
            try:
                return self.parent.get_method(name)
            except SemanticException:
                raise SemanticException(f'Method "{name}" is not defined in {self.name}.')

    # Define un metodo para el tipo actual con el nombre, los parametros y el tipo de
    # retorno correspondientes
    def define_method(self, name:str, param_names:list, param_types:list, return_type ):
        if name in self.methods:
            raise SemanticException(f'Method "{name}" already defined in {self.name}')

        method = self.methods[name] = Method(name, param_names, param_types, return_type)
        return method

    # Returns true if other is a parent of current type
    def inherits_from(self, other):
        return other.is_special_type() or self == other or (self.parent is not None and self.parent.inherits_from(other))

    def is_special_type(self):
        return False

    def __str__(self):
        output = f'type {self.name}'
        parent = '' if self.parent is None else f' : {self.parent.name}'
        output += parent
        output += ' {'
        output += '\n\t' if self.attributes or self.methods else ''
        output += '\n\t'.join(str(x) for x in self.attributes)
        output += '\n\t' if self.attributes else ''
        output += '\n\t'.join(str(x) for x in self.methods.values())
        output += '\n' if self.methods else ''
        output += '}\n'
        return output

    def __repr__(self):
        return str(self)

# Special_Types
class SelfType(Type):
    def __init__(self):
        Type.__init__(self, 'SELF_TYPE')
        self.sealed = True

    def inherits_from(self, other):
        return False

    def is_special_type(self):
        return True

    def __eq__(self, other):
        return isinstance(other, SelfType)

class AutoType(Type):
    def __init__(self):
        Type.__init__(self, 'AUTO_TYPE')
        self.sealed = True

    def union_type(self, other):
        return self

    def inherits_from(self, other):
        return True

    def is_special_type(self):
        return True

    def __eq__(self, other):
        return isinstance(other, Type)

class ErrorType(Type):
    def __init__(self):
        Type.__init__(self, '<error>')
        self.sealed = True

    def union_type(self, other):
        return self

    def inherits_from(self, other):
        return True

    def is_special_type(self):
        return True

    def __eq__(self, other):
        return isinstance(other, Type)

# Clase para representar una variable dentro del programa
class VariableInfo:
    def __init__(self, name, vtype):
        self.name = name
        self.type = vtype
        self.infered = not isinstance(vtype, AutoType)
        self.types = []

    # Incluye un tipo entre los tipos posibles de los que hereda la variable
    def set_type(self, typex):
        if not self.infered and not isinstance(typex, AutoType):
            self.types.append(typex)

    # Infiere el tipo de la variable, obtiene entre todos los tipos posibles
    # uno de los que hereden todos los tipos definidos anteriormente, basicamente
    # obtiene el lca de todos los tipos definidos anteriormente
    def infer_type(self):
        if not self.infered:
            self.type = None
            for typex in self.types:
                self.type = typex if not self.type else self.type.type_union(typex)

            if not self.type or isinstance(self.type, ErrorType):
                self.type = AutoType()

            self.infered = not isinstance(self.type, AutoType)
            self.types = []

            return self.infered

        return False

# Clase para representar el contexto en el que se guardan las variables y los
# tipos durante el chequeo semantico del programa
class Context:
    def __init__(self):
        self.types = {}

    # Incluye un tipo dentro del contexto
    def add_type(self, type : Type):
        if type.name in self.types:
            raise SemanticException(f'Type with the same name ({type.name}) already in context.')
        self.types[type.name] = type
        return type

    # Crea un tipo dentro del contexto
    def create_type(self, name : str):
        if name in self.types:
            raise SemanticException(f'Type with the same name ({name}) already in context.')
        type = self.types[name] = Type(name)
        return type

    # Obtiene un tipo del contexto con el nombre correspondiente
    def get_type(self, name : str):
        try:
            return self.types[name]
        except KeyError:
            raise SemanticException(f'Type ({name}) not defined.')

    def __str__(self):
        return '{\n\t' + '\n\t'.join(y for x in self.types.values() for y in str(x).split('\n')) + '\n}'

    def __repr__(self):
        return str(self)


# Clase para representar el scope durante el chequeo semantico
class Scope:
    def __init__(self, parent = None):
        self.parent = parent
        self.locals = []
        self.childs = []

    # Crea un scope hijo
    def create_child(self):
        self.childs.append(Scope(self))
        return self.childs[-1]

    # Define una variable en el scope
    def define_variable(self, name : str, type : Type):
        self.locals.append(VariableInfo(name, type))
        return self.locals[-1]

    # Retorna una variable definida en el scope, None si no esta definida
    def find_variable(self, name : str):
        try:
            return next(i for i in self.locals if i.name == name)
        except StopIteration:
            return self.parent.find_variable(name) if self.parent is not None else None

    # True si la variable esta definida en el scope
    def is_defined(self, name : str):
        return self.find_variable(name) is not None

    # True si la variable fue definida en el scope actual y no en alguno
    # de sus scope padres
    def is_local(self, name : str):
        return any(i for i in self.locals if i.name == name)

