import sys
import ply.yacc as yacc
from lexer import tokens
import os
import re

debug = True
jump_counter = 0

# ######## MEMORY MANAGEMENT ########

memory_count = 0
variables = {}
iter_variables = []
arrays = {}
inits = []
declared = []
square_used = False


# TMP VARIABLES USE:
# tmp0 never used, because code uses non stop

# tmp1-tmp63 contain values tmpi = i^2
# tmp64-tmp70 help construct lookup table

# tmp101 not used
# tmp102 not used
# tmp103 in holds recent evaluation
# tmp104 in value evaluation and in condition evaluation
# tmp105 in value evaluation and in condition evaluation
# tmp106 in value evaluation
# tmp107 in value evaluation
# tmp108 in value evaluation
# tmp109 in value evaluation
# tmp110 in assign and read
# tmp111 in values eval
# tmp112 holds constant 1 used in shift to make multiply * 2
# tmp113 holds constant -1 used in shift to make floor(multiply * 1/2)
# tmp114 holds constant 6 if times used
# tmp115 holds constant -6 if times used

def add_variable(id, lineno):
    if id in inits:
        raise Exception('Blad w linii {} : Druga deklaracja {}'.format(lineno, id))
    global memory_count
    variables[id] = memory_count
    inits.append(id)
    memory_count += 1

def add_array(id, start, stop, lineno):
    if id in inits:
        raise Exception('Blad w linii {} : Druga deklaracja {}'.format(lineno, id))
    if start > stop:
        raise Exception('Blad w linii {}: Niewlasciwy zakres tablicy {}'.format(lineno, id))
    global memory_count
    arrays[id] = [memory_count, start, stop]
    inits.append(id)
    memory_count += (stop - start + 1)

for i in range(120):
    add_variable(id='tmp@{}'.format(i), lineno='init_tmp')

# ######## HELPERS ########

def load_value_to_adres(value, adres, lineno):
    if value[0] == 'num':
        return put_const_to_adres(value[1], adres)
    elif value[0] == 'id':
        if value[1] in variables:
            if adres == 0:
                return cmd(['LOAD ' + str(get_id_adress(value))])
            else:
                return cmd([
                    'LOAD ' + str(get_id_adress(value)),
                    'STORE ' + str(adres)
                ])
        else:
            pass  # throw undeclared except
    elif value[0] == 'tab':
        if value[2][0] == 'num':
            if adres == 0:
                return cmd(['LOAD ' + str(get_id_adress(value))])
            else:
                return cmd([
                    'LOAD ' + str(get_id_adress(value)),
                    'STORE ' + str(adres)
                ])
        if value[2][0] == 'id':
            if adres == 0:
                return cmd([
                    'LOAD ' + str(get_id_adress(value[2])),
                    'ADD ' + str(get_id_adress(('id', value[1] + '@mem_adr_offseted'))),
                    'LOADI 0',
                ], 'arr_id_val_adr')
            else:
                return cmd([
                    'LOAD ' + str(get_id_adress(value[2])),
                    'ADD ' + str(get_id_adress(('id', value[1] + '@mem_adr_offseted'))),
                    'LOADI 0',
                    'STORE ' + str(adres),
                ], 'arr_id_val_adr')
    else:
        raise Exception("Cannot load value to adres, type not recognized. Line {}".format(lineno))

def gen_squares_lookup():
    pow = 6
    cmd_list = []
    cmd_list.append('SUB 0')
    cmd_list.append('INC')

    for i in range(2, 2 + 2**pow):
        cmd_list.append('STORE ' + str(i))
        cmd_list.append('INC')
        cmd_list.append('INC')

    cmd_list = cmd_list[:-2]

    cmd_list.append('SUB 0')
    cmd_list.append('INC')
    cmd_list.append('STORE 1')

    for i in range(2, 2 ** pow):
        cmd_list.append('ADD ' + str(i+1))
        cmd_list.append('STORE ' + str(i))

    return cmd(cmd_list, 'genlook')

def put_const_to_adres(num, adres):
    commands = ['SUB 0']
    positive = num > 0
    num = abs(num)
    num = str(bin(num))[2:]  # to binary

    for i in range(len(num)):
        if i != 0:
            commands.append('SHIFT 112')

        if num[i] == '1':
            if positive:
                commands.append('INC')
            else:
                commands.append('DEC')

    if adres != 0:
        commands.append('STORE {}'.format(adres))

    return cmd(commands, 'cnst')

def get_id_adress(id, check_iter_modification=False):
    if check_iter_modification:
        if id[0] == 'id':
            if id[1] in iter_variables:
                raise Exception('Cannot assign to iterator')

    if id[0] == 'id':
        return variables[id[1]]
    elif id[0] == 'tab':
        if id[2][0] == 'num':
            return arrays[id[1]][0] + (id[2][1] - arrays[id[1]][1])
        else:
            return arrays[id[1]][0]

def gen_jump_labels(n):
    global jump_counter
    jump_lines = []
    jump_instructions = []

    for _ in range(n):
        jump_lines.append('@JL{}'.format(jump_counter))
        jump_instructions.append('@JI{}'.format(jump_counter))
        jump_counter += 1

    return jump_lines, jump_instructions

def cmd(cmd_list, opname=None):
    unpacked_list = []

    for cmd_el in cmd_list:
        if isinstance(cmd_el, list):
            for list_el in cmd_el:
                unpacked_list.append(list_el)
        else:
            unpacked_list.append(cmd_el)

    prefixed_list = []

    if opname is not None:
        opname = '[' + opname + '] '
    else:
        opname = ''

    for idx, un_list_el in enumerate(unpacked_list):
        if idx == 0:
            prefix_str = opname
        else:
            prefix_str = len(opname) * ' '

        if isinstance(un_list_el, str):
            prefixed_list.append({'prefix': prefix_str, 'instr': un_list_el})
        elif isinstance(un_list_el, dict):
            prefixed_list.append({'prefix': prefix_str + un_list_el['prefix'], 'instr': un_list_el['instr']})

    return prefixed_list

def build_cmd_to_code_pseudocode(prefixed_list):
    lines = [(el['prefix'] + el['instr']) for el in prefixed_list]

    return '\n'.join(lines)

def build_cmd_to_code_machinecode(prefixed_list):
    instr_list = [el['instr'].strip() for el in prefixed_list]
    JL_to_instr_count = {}
    instr_count = 0
    instr_list_no_JL = []
    instr_list_no_JL_no_JI = []

    for instr in instr_list:
        if instr[:3] == '@JL':
            JL_to_instr_count[instr[3:]] = instr_count
        else:
            instr_count += 1
            instr_list_no_JL.append(instr)

    for instr in instr_list_no_JL:
        if instr.split(' ')[-1][:3] == '@JI':
            jump_JI_num = instr.split(' ')[-1][3:]
            jump_type = instr.split(' ')[0]
            changed_command = jump_type + ' ' + str(JL_to_instr_count[jump_JI_num])
            instr_list_no_JL_no_JI.append(changed_command)
        else:
            instr_list_no_JL_no_JI.append(instr)

    return '\n'.join(instr_list_no_JL_no_JI)

# ######## PARSER ########

def p_program_with_declarations(p):
    """program : DECLARE declarations BEGIN commands END"""
    if square_used:
        p[0] = cmd([
            gen_squares_lookup(),
            'SUB 0',
            'DEC',
            'STORE 113',  # gen -1
            'INC',
            'INC',
            'STORE 112',  # gen 1
            'INC',
            'INC',
            'INC',
            'INC',
            'INC',
            'STORE 114',  # gen 6
            'SUB 0',
            'SUB 114',
            'STORE 115',  # gen -6
            p[2],
            p[4],
            'HALT',
        ], 'prog')
    else:
        p[0] = cmd([
            'SUB 0',
            'DEC',
            'STORE 113',
            'INC',
            'INC',
            'STORE 112',
            p[2],
            p[4],
            'HALT',
        ], 'prog')

def p_program_without_declarations(p):
    """program : BEGIN commands END"""

    if square_used:
        p[0] = cmd([
            gen_squares_lookup(),
            'SUB 0',
            'DEC',
            'STORE 113',  # gen -1
            'INC',
            'INC',
            'STORE 112',  # gen 1
            'INC',
            'INC',
            'INC',
            'INC',
            'INC',
            'STORE 114',  # gen 6
            'SUB 0',
            'SUB 114',
            'STORE 115',  # gen -6
            p[2],
            'HALT',
        ], 'prog')
    else:
        p[0] = cmd([
            'SUB 0',
            'DEC',
            'STORE 113',
            'INC',
            'INC',
            'STORE 112',
            p[2],
            'HALT',
        ], 'prog')

def p_declarations_commasep_single(p):
    """declarations : declarations COMMA ID"""
    p[0] = cmd([
        p[1],
    ])
    add_variable(p[3], p.lineno(3))

def p_declarations_commasep_array(p):
    """declarations : declarations COMMA ID LBR NUM COLON NUM RBR"""
    arr_id = p[3]
    arr_adres_offseted_id = p[3] + '@mem_adr_offseted'
    arr_beg = p[5]
    arr_end = p[7]
    add_array(arr_id, arr_beg, arr_end, p.lineno(3))
    add_variable(arr_adres_offseted_id, p.lineno(3))

    #  tabname@mem_adr_offseted has offseted adres

    if p[1] is not None:
        p[0] = cmd([
            p[1],
            put_const_to_adres(arrays[arr_id][0] - arr_beg, variables[arr_adres_offseted_id]),
        ], 'decl')
    else:
        p[0] = cmd([
            put_const_to_adres(arrays[arr_id][0] - arr_beg, variables[arr_adres_offseted_id]),
        ], 'decl')

def p_declarations_single(p):
    """declarations : ID"""
    p[0] = None
    add_variable(p[1], p.lineno(1))

def p_declarations_array(p):
    """declarations : ID LBR NUM COLON NUM RBR"""
    arr_id = p[1]
    arr_adres_offseted_id = p[1] + '@mem_adr_offseted'
    arr_beg = p[3]
    arr_end = p[5]
    add_array(arr_id, arr_beg, arr_end, p.lineno(3))
    add_variable(arr_adres_offseted_id, p.lineno(3))

    #  tabname@mem_adr_offseted has offseted adres

    p[0] = cmd([
        put_const_to_adres(arrays[arr_id][0] - arr_beg, variables[arr_adres_offseted_id])
    ], 'decl')

def p_commands_many(p):
    """commands : commands command"""
    p[0] = cmd([
        p[1],
        p[2],
    ])

def p_commands_single(p):
    """commands : command"""
    p[0] = cmd([
        p[1]
    ])

def p_command_assign(p):
    """command : identifier ASSIGN expression SEMICOLON"""
    # after evaluating expression result is in tmp0

    if p[1][0] == 'tab' and p[1][2][0] == 'id':
        p[0] = cmd([
            'LOAD ' + str(get_id_adress(p[1][2])),  # load n to memory
            'ADD ' + str(get_id_adress(('id', p[1][1] + '@mem_adr_offseted'))),
            'STORE 110',
            p[3],
            'STOREI 110'
        ], 'assgn')
    else:
        p[0] = cmd([
            p[3],
            'STORE ' + str(get_id_adress(p[1], check_iter_modification=True)),
        ], 'assgn')

def p_command_if_then_else(p):
    """command : IF condition THEN commands ELSE commands ENDIF"""
    # condition is evaluated into tmp0 positive value is True negative or zero False
    JL, JI = gen_jump_labels(2)

    p[0] = cmd([
        p[2],
        'JNEG ' + JI[0],
        'JZERO ' + JI[0],
        p[4],
        'JUMP ' + JI[1],
        JL[0],
        p[6],
        JL[1],
    ], 'ifel')

def p_command_if_then(p):
    """command : IF condition THEN commands ENDIF"""
    # condition is evaluated into tmp0 positive value is True negative or zero False
    JL, JI = gen_jump_labels(1)

    p[0] = cmd([
        p[2],
        'JNEG ' + JI[0],
        'JZERO ' + JI[0],
        p[4],
        JL[0],
    ], 'if')

def p_command_while_do(p):
    """command : WHILE condition DO commands ENDWHILE"""
    # condition is evaluated into tmp0 positive value is True negative or zero False
    JL, JI = gen_jump_labels(3)

    p[0] = cmd([
        JL[1],
        p[2],
        'JPOS ' + JI[2],
        'JUMP ' + JI[0],
        JL[2],
        p[4],
        'JUMP ' + JI[1],
        JL[0],
    ], 'whldo')

def p_command_do_while(p):
    """command : DO commands WHILE condition ENDDO"""
    # condition is evaluated into tmp0 positive value is True negative or zero False
    JL, JI = gen_jump_labels(2)

    p[0] = cmd([
        JL[0],
        p[2],
        p[4],
        'JPOS ' + JI[0],
    ], 'dowhl')

def p_iterator(p):
    '''iterator	: ID '''
    iter_id = p[1]
    bound_id = p[1] + '@bound'
    add_variable(iter_id, p.lineno(1))
    add_variable(bound_id, p.lineno(1))
    iter_variables.append(iter_id)
    p[0] = p[1]

def p_command_for_to(p):
    """command : FOR iterator FROM value TO value DO commands ENDFOR"""

    JL, JI = gen_jump_labels(3)
    iter_id = p[2]
    bound_id = p[2] + '@bound'

    p[0] = cmd([
        load_value_to_adres(p[4], get_id_adress(("id", iter_id)), p.lineno(1)),
        load_value_to_adres(p[6], get_id_adress(("id", bound_id)), p.lineno(1)),

        JL[1],
        'LOAD ' + str(get_id_adress(("id", bound_id))),
        'SUB ' + str(get_id_adress(("id", iter_id))),
        'JNEG ' + JI[2],

        p[8],
        'LOAD ' + str(get_id_adress(("id", iter_id))),
        'INC',
        'STORE ' + str(get_id_adress(("id", iter_id))),  # iter = iter + 1
        'JUMP ' + JI[1],  # back to loop
        JL[2],

    ], 'forto')

    iter_variables.remove(iter_id)
    del variables[iter_id]
    inits.remove(iter_id)
    del variables[bound_id]
    inits.remove(bound_id)

def p_command_for_downto(p):
    """command : FOR iterator FROM value DOWNTO value DO commands ENDFOR"""

    JL, JI = gen_jump_labels(3)
    iter_id = p[2]
    bound_id = p[2] + '@bound'

    p[0] = cmd([
        load_value_to_adres(p[4], get_id_adress(("id", iter_id)), p.lineno(1)),
        load_value_to_adres(p[6], get_id_adress(("id", bound_id)), p.lineno(1)),

        JL[1],
        'LOAD ' + str(get_id_adress(("id", bound_id))),
        'SUB ' + str(get_id_adress(("id", iter_id))),
        'JPOS ' + JI[2],
        p[8],
        'LOAD ' + str(get_id_adress(("id", iter_id))),
        'DEC',
        'STORE ' + str(get_id_adress(("id", iter_id))),  # iter = iter - 1
        'JUMP ' + JI[1],  # back to loop
        JL[2],

    ], 'fordwnt')

    iter_variables.remove(iter_id)
    del variables[iter_id]
    inits.remove(iter_id)
    del variables[bound_id]
    inits.remove(bound_id)

def p_command_read(p):
    """command : READ identifier SEMICOLON"""
    if p[2][0] == 'tab' and p[2][2][0] == 'id':
        p[0] = cmd([
            'LOAD ' + str(get_id_adress(p[2][2])),  # load n to memory
            'ADD ' + str(get_id_adress(('id', p[2][1] + '@mem_adr_offseted'))),
            'STORE 110',
            'GET',
            'STOREI 110',
        ], 'read')
    else:
        p[0] = cmd([
            'GET',
            'STORE ' + str(get_id_adress(p[2], check_iter_modification=True)),
        ], 'assgn')

def p_command_write(p):
    """command : WRITE value SEMICOLON"""

    p[0] = cmd([
        load_value_to_adres(p[2], 0, p.lineno(1)),
        'PUT'
    ], 'wrt')

def p_expression_val(p):
    """expression : value"""
    p[0] = cmd([
        load_value_to_adres(p[1], 0, p.lineno(1)),
    ])

def p_expression_val_plus(p):
    """expression : value PLUS value"""

    if p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'INC',
        ], 'plus')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'INC',
            'INC',
        ], 'plus')
    else:
        p[0] = cmd([
            load_value_to_adres(p[1], 101, p.lineno(1)),
            load_value_to_adres(p[3], 0, p.lineno(3)),
            'ADD 101',
        ], 'plus')

def p_expression_val_minus(p):
    """expression : value MINUS value"""

    if p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'DEC',
        ], 'minus')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'DEC',
            'DEC',
        ], 'minus')
    else:
        p[0] = cmd([
            load_value_to_adres(p[3], 101, p.lineno(1)),
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'SUB 101',
        ], 'minus')

def p_expression_val_times(p):
    """expression : value TIMES value"""
    # tmp103 contains number to add
    # tmp104 contains counter
    # tmp105 contains i
    # tmp106 contains sum
    # tmp107 used in swap
    # tmp108 number of negative signs of a and b

    # tmp112 holds constant 1 used in shift to make multiply * 2
    # tmp113 holds constant -1 used in shift to make floor(multiply * 1/2)
    # tmp114 holds constant 6
    # tmp115 holds constant -6

    global square_used

    JL, JI = gen_jump_labels(30)
    if p[1] == p[3]:
        square_used = True

        p[0] = cmd([
            load_value_to_adres(p[1], 103, p.lineno(1)),
            load_value_to_adres(p[3], 104, p.lineno(3)),

            'LOAD 103',
            'JPOS ' + JI[16],
            'JZERO ' + JI[20],
            'SUB 0',
            'SUB 103',
            'STORE 103',
            'STORE 104',
            JL[16],  # changed sign of a and b to positive

            'SHIFT 115',  # div 2^6
            'JPOS ' + JI[0],  ## case when a was >= 2^6

            'SHIFT 114',  # 2^6 * (n div 2^6)
            'STORE 107',
            'LOAD 103',
            'SUB 107',
            'LOADI 0',  # (n mod 2^6)^2
            'JUMP ' + JI[20],

            JL[0],

            'STORE 103',  # updated a
            'SHIFT 114',  # 2^6 * (n div 2^6)
            'STORE 107',
            'LOAD 104',
            'SUB 107',
            'STORE 108',  # n mod 2^6
            'LOADI 0',  # (n mod 2^6)^2
            'STORE 106',  # sum initialized with square

            'LOAD 104',
            'ADD 108',
            'SHIFT 114',
            'STORE 104', # updated b

            'SUB 0',
            'STORE 105',

            'LOAD 103',

            JL[2],
            'SHIFT 113',
            'SHIFT 112',
            'SUB 103',  # calculate bit

            'JZERO ' + JI[4],
            'LOAD 104',
            'SHIFT 105',
            'ADD 106',
            'STORE 106',
            JL[4],  # if bit<0 sum = sum + 2**i * b

            'LOAD 105',
            'INC',
            'STORE 105',  # i = i + 1

            'LOAD 103',
            'SHIFT 113',
            'STORE 103',  # a = floor(a/2)
            'JPOS ' + JI[2],

            JL[19],
            'LOAD 106',
            JL[20],

        ], 'pow2')


    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'SHIFT 112',  # HERE 2*val_1
        ], 'tms')
    elif p[1][0] == 'num' and int(p[1][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[3], 0, p.lineno(1)),
            'SHIFT 112',  # HERE 2*val_1
        ], 'tms')
    else:
        p[0] = cmd([
            load_value_to_adres(p[1], 103, p.lineno(1)),
            load_value_to_adres(p[3], 104, p.lineno(3)),

            'SUB 0',
            'STORE 105',  # initialize i
            'STORE 106',  # initialize sum
            'STORE 108',  # initialize signs

            'LOAD 103',
            'JPOS ' + JI[16],
            'JZERO ' + JI[19],
            'SUB 0',
            'SUB 103',
            'STORE 103',
            'LOAD 108',
            'INC',
            'STORE 108',
            JL[16],  # changed sign of a

            'LOAD 104',
            'JPOS ' + JI[15],
            'JZERO ' + JI[19],
            'SUB 0',
            'SUB 104',
            'STORE 104',
            'LOAD 108',
            'INC',
            'STORE 108',
            JL[15],  # changed sign of b

            'LOAD 103',
            'SUB 104',
            'JPOS ' + JI[13],


            # HERE LOOP BODY FIRST TYPE a<b
            'LOAD 103',

            JL[2],
            'SHIFT 113',
            'SHIFT 112',
            'SUB 103',  # calculate bit

            'JZERO ' + JI[4],
            'LOAD 104',
            'SHIFT 105',
            'ADD 106',
            'STORE 106',
            JL[4],  # if bit<0 sum = sum + 2**i * b

            'LOAD 105',
            'INC',
            'STORE 105',  # i = i + 1

            'LOAD 103',
            'SHIFT 113',
            'STORE 103',  # a = floor(a/2)
            'JPOS ' + JI[2],

            # END OF CALCULATING LOOP FIRST TYPE a<b

            'JUMP ' + JI[14],
            JL[13],

            # HERE LOOP BODY SECOND TYPE a>b
            'LOAD 104',

            JL[22],
            'SHIFT 113',
            'SHIFT 112',
            'SUB 104',  # calculate bit

            'JZERO ' + JI[24],
            'LOAD 103',
            'SHIFT 105',
            'ADD 106',
            'STORE 106',
            JL[24],  # if bit<0 sum = sum + 2**i * b

            'LOAD 105',
            'INC',
            'STORE 105',  # i = i + 1

            'LOAD 104',
            'SHIFT 113',
            'STORE 104',  # a = floor(a/2)
            'JPOS ' + JI[22],

            # END OF CALCULATING LOOP SECOND TYPE a>b

            JL[14],
            'LOAD 108',
            'DEC',
            'JNEG ' + JI[17],
            'JPOS ' + JI[17],
            'SUB 0',
            'SUB 106',
            'JUMP ' + JI[19],  # flipping the sign of abs(a*b) depending on initial signs of a and b
            JL[17],
            'LOAD 106',
            JL[19],
        ], 'tms')

def p_expression_val_div(p):
    """expression : value DIV value"""

    # tmp3 contains a later aMODb later aDIVb
    # tmp4 contains b
    # tmp5 contains sign(a)
    # tmp6 contains sign(b)
    # tmp7 contains div
    # tmp8 contains current power used
    # tmp9 used mainly to do subtraction of two expressions

    JL, JI = gen_jump_labels(20)

    if p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'SHIFT 113',
        ], 'div')
    else:
        p[0] = cmd([
                   load_value_to_adres(p[1], 103, p.lineno(1)),
                   load_value_to_adres(p[3], 104, p.lineno(3)),
                   'LOAD 103',
                   'JZERO ' + JI[0],
                   'LOAD 104',
                   'JZERO ' + JI[0],  # checking if a or b is zero if is then exit
                   'DEC',
                   'DEC',
                   'JZERO ' + JI[10],

                   'SUB 0',
                   'JZERO ' + JI[2],  # else go to regular a%b

                   JL[0],
                   'STORE 107',
                   'JZERO ' + JI[1],  # code if a or b is zero return 0,0

                   JL[2],
                   # START REGULAR aMODb a!=0 and b!=0

                   'INC',
                   'STORE 105',
                   'STORE 106',  # default a,b are pos

                   'LOAD 103',
                   'JPOS ' + JI[3],
                   'SUB 0',
                   'STORE 105',
                   'SUB 103',
                   'STORE 103',
                   JL[3],  # changed tmp3 to abs(a) and changed tmp5 to 0 if a<0

                   'LOAD 104',
                   'JPOS ' + JI[4],
                   'SUB 0',
                   'STORE 106',
                   'SUB 104',
                   'STORE 104',
                   JL[4],  # changed tmp4 to abs(b) and tmp6 to 0 if b<0

                   # ALGO START REGULAR aMODb a!=0 and b!=0

                   # START FIRST WHILE

                   'SUB 0',
                   'DEC',
                   'STORE 108',  # tmp8 is power i

                   'INC',
                   'SUB 103',
                   'STORE 103',

                   JL[5],
                   'LOAD 108',
                   'INC',
                   'STORE 108',

                   'LOAD 104',
                   'SHIFT 108',
                   'ADD 103',
                   'STORE 103',

                   'JNEG ' + JI[5],
                   'JZERO ' + JI[5],

                   'LOAD 104',
                   'SHIFT 108',
                   'STORE 109',
                   'LOAD 103',
                   'SUB 109',
                   'STORE 103',  # correction to modulo while does one too much subtraction

                   # END FIRST WHILE

                   'SUB 0',
                   'INC',
                   'SHIFT 108',
                   'DEC',
                   'STORE 107',  # first div initialization in tmp7

                   # START SECOND WHILE

                   JL[6],
                   JL[7],

                   'SUB 0',
                   'INC',
                   'SHIFT 108',
                   'ADD 107',
                   'STORE 107',  # div calculated in loop

                   'LOAD 104',
                   'SHIFT 108',
                   'ADD 103',
                   'STORE 103',  # md calculated in loop
                   'DEC',
                   'JNEG ' + JI[7],

                   'SUB 0',
                   'INC',
                   'SHIFT 108',
                   'STORE 109',
                   'LOAD 107',
                   'SUB 109',
                   'STORE 107',  # div corrected after loop

                   'LOAD 104',
                   'SHIFT 108',
                   'STORE 109',
                   'LOAD 103',
                   'SUB 109',
                   'STORE 103',  # md corrected after loop

                   'LOAD 108',
                   'JZERO ' + JI[12],  # becomes -1
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'JPOS ' + JI[15],  # stays as is
                   JL[12],
                   'DEC',
                   JL[15],
                   'STORE 108',  # power i decreased after loop by factor (some depends on setting)

                   'JPOS ' + JI[6],
                   'JZERO ' + JI[6],

                   # END SECOND WHILE

                   'LOAD 105',
                   'SUB 106',

                   'JZERO ' + JI[8], # if a and b have diffrent signs we exec code here
                   'LOAD 103',
                   'JZERO ' + JI[9],  # if md!=0 we make bunch of correction stuff
                   'SUB 0',
                   'SUB 107',
                   'DEC',
                   'STORE 107',
                   'JUMP ' + JI[8],
                   JL[9],
                   'SUB 107',
                   'STORE 107',
                   JL[8],

                   'JUMP ' + JI[1],

                   # END OF REGULAR algo a!=0 b!=0 b!=2

                   ###### HERE WE MAKE ALGO WHEN b == 2

                   JL[10],

                   'LOAD 103',  # HERE we calculate div when b == 2
                   'SHIFT 113',
                   'STORE 107',

                   JL[1],
                   'LOAD 107',

                   # END ALGO 3 contains aDIVb

               ], 'div')

def p_expression_val_mod(p):
    """expression : value MOD value"""

    # tmp3 contains a later aMODb
    # tmp4 contains b
    # tmp5 contains sign(a)
    # tmp6 contains sign(b)
    # tmp7 not used
    # tmp8 contains current power used
    # tmp9 used mainly to do subtraction of two expressions

    JL, JI = gen_jump_labels(20)

    if p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 103, p.lineno(1)),
            'SHIFT 113',  # HERE we calculate div when b == 2
            'SHIFT 112',  # HERE 2*DIV
            'STORE 107',
            'LOAD 103',
            'SUB 107',
        ], 'mod')
    else:
        p[0] = cmd([
                   load_value_to_adres(p[1], 103, p.lineno(1)),
                   load_value_to_adres(p[3], 104, p.lineno(3)),
                   'LOAD 104',
                   'JZERO ' + JI[1],  # checking if a or b is zero if is then exit
                   'DEC',
                   'DEC',
                   'JZERO ' + JI[19],

                   # START REGULAR aMODb a!=0 and b!=0

                   'SUB 0',
                   'INC',
                   'STORE 105',
                   'STORE 106',  # default a,b are pos

                   'LOAD 103',
                   'JPOS ' + JI[3],
                   'SUB 0',
                   'STORE 105',
                   'SUB 103',
                   'STORE 103',
                   JL[3],  # changed tmp3 to abs(a) and changed tmp5 to 0 if a<0

                   'LOAD 104',
                   'JPOS ' + JI[4],
                   'SUB 0',
                   'STORE 106',
                   'SUB 104',
                   'STORE 104',
                   JL[4],  # changed tmp4 to abs(b) and tmp6 to 0 if b<0

                   # ALGO START REGULAR aMODb a!=0 and b!=0

                   # START FIRST WHILE

                   'SUB 0',
                   'DEC',
                   'DEC',
                   'STORE 108',  # tmp8 is power i

                   'INC',
                   'INC',
                   'SUB 103',
                   'STORE 103',

                   JL[5],
                   'LOAD 108',
                   'INC',
                   'INC',
                   'INC',
                   'INC',
                   'STORE 108',

                   'LOAD 104',
                   'SHIFT 108',
                   'ADD 103',
                   'STORE 103',

                   'JNEG ' + JI[5],
                   'JZERO ' + JI[5],

                   'LOAD 104',
                   'SHIFT 108',
                   'STORE 109',
                   'LOAD 103',
                   'SUB 109',
                   'STORE 103',  # correction to modulo while does one too much subtraction

                   # END FIRST WHILE

                   'LOAD 108',
                   'JZERO ' + JI[12],  # becomes -1
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'JPOS ' + JI[15],  # stays as is
                   JL[12],
                   'DEC',
                   JL[15],
                   'STORE 108',

                   # START SECOND WHILE

                   JL[6],
                   JL[7],
                   'LOAD 104',
                   'SHIFT 108',
                   'ADD 103',
                   'STORE 103',  # md calculated in loop

                   'JNEG ' + JI[7],
                   'JZERO ' + JI[7],

                   'LOAD 104',
                   'SHIFT 108',
                   'STORE 109',
                   'LOAD 103',
                   'SUB 109',
                   'STORE 103',  # md corrected after loop

                   'LOAD 108',
                   'JZERO ' + JI[12],  # becomes -1
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'DEC',
                   'JZERO ' + JI[15],  # becomes 0
                   'JPOS ' + JI[15],  # stays as is
                   JL[12],
                   'DEC',
                   JL[15],
                   'STORE 108',  # power i decreased after loop by factor (some depends on setting)

                   'INC',
                   'JPOS ' + JI[6],

                   'SUB 103',
                   'STORE 103',

                   # END SECOND WHILE

                   'LOAD 105',
                   'SUB 106',

                   'JZERO ' + JI[8],  # if a and b have diffrent signs we exec code here
                   'LOAD 103',
                   'JZERO ' + JI[9],  # if md!=0 we make bunch of correction stuff
                   'LOAD 104',
                   'SUB 103',
                   'STORE 103',
                   JL[9],
                   JL[8],

                   'LOAD 106',
                   'JPOS ' + JI[10],
                   'SUB 103',
                   'STORE 103',
                   JL[10],

                   'JUMP ' + JI[18],

                   JL[19],

                   'LOAD 103',
                   'SHIFT 113',  # HERE we calculate div when b == 2
                   'SHIFT 112',  # HERE 2*DIV
                   'STORE 107',
                   'LOAD 103',
                   'SUB 107',
                   'STORE 103',

                   JL[18],
                   'LOAD 103',
                   JL[1],

               ], 'mod')

def p_condition_val_eq(p):
    """condition : value EQ value"""
    # after evaluation p0 contains 0 or 1 1 if true 0 if false
    JL, JI = gen_jump_labels(20)

    if p[3][0] == 'num' and int(p[3][1]) == -2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'INC',
            'INC',
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')
    elif p[3][0] == 'num' and int(p[3][1]) == -1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'INC',
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 0:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'DEC',
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(1)),
            'DEC',
            'DEC',
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')
    else:
        p[0] = cmd([
            load_value_to_adres(p[1], 101, p.lineno(1)),
            load_value_to_adres(p[3], 0, p.lineno(3)),
            'SUB 101',
            'JZERO ' + JI[0],
            'JNEG ' + JI[1],
            'SUB 0',
            'DEC',
            JL[1],
            JL[0],
            'INC',
        ], 'veqv')

def p_condition_val_neq(p):
    """condition : value NEQ value"""
    # after evaluation p0 contains 0 or 1 1 if true 0 if false
    JL, JI = gen_jump_labels(20)

    if p[3][0] == 'num' and int(p[3][1]) == -2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
            'INC',
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')
    elif p[3][0] == 'num' and int(p[3][1]) == -1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 0:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'DEC',
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'DEC',
            'DEC',
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')
    else:
        p[0] = cmd([
            load_value_to_adres(p[1], 101, p.lineno(1)),
            load_value_to_adres(p[3], 0, p.lineno(3)),
            'SUB 101',
            'JPOS ' + JI[0],
            'JZERO ' + JI[0],
            'SHIFT 0',
            'INC',
            'INC',
            JL[0],
        ], 'vneqv')

def p_condition_val_le(p):
    """condition : value LE value"""

    p[0] = cmd([
        load_value_to_adres(p[1], 101, p.lineno(1)),
        load_value_to_adres(p[3], 0, p.lineno(3)),
        'SUB 101',
    ], 'vlev')

def p_condition_val_ge(p):
    """condition : value GE value"""

    if p[3][0] == 'num' and int(p[3][1]) == -2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
            'INC',
        ], 'vgev')
    elif p[3][0] == 'num' and int(p[3][1]) == -1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
        ], 'vgev')
    elif p[3][0] == 'num' and int(p[3][1]) == 0:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
        ], 'vgev')
    elif p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'DEC',
        ], 'vgev')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'DEC',
            'DEC',
        ], 'vgev')
    else:
        p[0] = cmd([
            load_value_to_adres(p[3], 101, p.lineno(1)),
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'SUB 101',
        ], 'vgev')

def p_condition_val_leq(p):
    """condition : value LEQ value"""

    p[0] = cmd([
        load_value_to_adres(p[1], 101, p.lineno(1)),
        load_value_to_adres(p[3], 0, p.lineno(3)),
        'SUB 101',
        'INC',
    ], 'vleqv')

def p_condition_val_geq(p):
    """condition : value GEQ value"""

    if p[3][0] == 'num' and int(p[3][1]) == -2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
            'INC',
            'INC',
        ], 'vgeqv')
    elif p[3][0] == 'num' and int(p[3][1]) == -1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
            'INC',
        ], 'vgeqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 0:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'INC',
        ], 'vgeqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 1:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
        ], 'vgeqv')
    elif p[3][0] == 'num' and int(p[3][1]) == 2:
        p[0] = cmd([
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'DEC',
        ], 'vgeqv')
    else:
        p[0] = cmd([
            load_value_to_adres(p[3], 101, p.lineno(1)),
            load_value_to_adres(p[1], 0, p.lineno(3)),
            'SUB 101',
            'INC',
        ], 'vgeqv')

def p_value_num(p):
    """value : NUM"""
    p[0] = ("num", p[1])

def p_value_id(p):
    """value : identifier"""
    p[0] = p[1]

def p_identifier_id(p):
    """identifier : ID"""
    p[0] = ("id", p[1])

def p_identifier_id_of_id(p):
    """identifier : ID LBR ID RBR"""
    p[0] = ("tab", p[1], ("id", p[3]))

def p_identifier_id_of_num(p):
    """identifier : ID LBR NUM RBR"""
    p[0] = ("tab", p[1], ("num", p[3]))

def p_error(p):
    print(p)
    sys.exit("error sys.exit")

parser = yacc.yacc()

def parse_file(imp_input_path, mr_output_path):
    with open(imp_input_path, 'r') as f_in:
        code_dev = f_in.read()
        list_code_repr = parser.parse(code_dev)
    with open(mr_output_path, 'w') as f_out:
        code_dev_machine = build_cmd_to_code_machinecode(list_code_repr)
        f_out.write(code_dev_machine)
