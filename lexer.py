import ply.lex as lex
import sys

tokens = [
    'DECLARE', 'BEGIN', 'END', 'SEMICOLON', 'COMMA',    # 0 program
    'NUM',                                              # 1 numbers
    'PLUS', 'MINUS', 'TIMES', 'DIV', 'MOD',             # 2 operators
    'EQ', 'NEQ', 'LE', 'GE', 'LEQ', 'GEQ',              # 3 relations
    'ASSIGN',                                           # 4 assign
    'LBR', 'RBR', 'COLON',                              # 5 arrays
    'IF', 'THEN', 'ELSE', 'ENDIF',                      # 6 if
    'WHILE', 'DO', 'ENDWHILE', 'ENDDO',                 # 7 while
    'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',            # 8 for
    'READ', 'WRITE',                                    # 9 read/write
    'ID'                                                # 10 identificators
]

# 0 program
t_ignore_COM = r'\[[^\]\[]*\]'
t_DECLARE = r'DECLARE'
t_BEGIN = r'BEGIN'
t_END = r'END'
t_SEMICOLON = r';'
t_COMMA = r','

# 1 numbers
def t_NUM(t):
    r'[-+]?[0-9]+'

    t.value = int(t.value)
    return t


# 2 operators
t_PLUS = r'PLUS'
t_MINUS = r'MINUS'
t_TIMES = r'TIMES'
t_DIV = r'DIV'
t_MOD = r'MOD'

# 3 relations
t_EQ = r'EQ'
t_NEQ = r'NEQ'
t_LE = r'LE'
t_GE = r'GE'
t_LEQ = r'LEQ'
t_GEQ = r'GEQ'

# 4 assign
t_ASSIGN = r'ASSIGN'

# 5 arrays
t_LBR = r'\('
t_RBR = r'\)'
t_COLON = r':'

# 6 if
t_IF = r'IF'
t_THEN = r'THEN'
t_ELSE = r'ELSE'
t_ENDIF = r'ENDIF'

# 7 while
t_WHILE = 'WHILE'
t_DO = 'DO'
t_ENDWHILE = 'ENDWHILE'
t_ENDDO = 'ENDDO'

# 8 for
t_FOR = 'FOR'
t_FROM = 'FROM'
t_TO = 'TO'
t_DOWNTO = 'DOWNTO'
t_ENDFOR = 'ENDFOR'

# 9 read/write
t_READ = 'READ'
t_WRITE = 'WRITE'

# 10 identificators
t_ID = r'[_a-z]+'

# Define a rule so we can track line NUMs
def t_newline(t):
    r'\r?\n+'
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'


# Error handling rule
def t_error(t):
    sys.exit("Illegal character '{}'".format(t.value[0]))
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()