import sys
import ply.yacc as yacc
from lexer import tokens
import copy

iter_num = 0
declared = []
error_log = []

def change_value_assign(value):
    tmp_value = copy.deepcopy(value)

    if len(tmp_value) == 0:
        raise Exception("Can't change value to assign, empty value")

    if tmp_value[0][0] == 'id':
        tmp_value[0][3] = 'asgn'
    elif tmp_value[0][0] == 'tab_id':
        tmp_value[0][0] = 'tab'
        tmp_value[0][3] = 'asgn'
        tmp_value[1][3] = 'ref'
    elif tmp_value[0][0] == 'tab_num':
        tmp_value[0][0] = 'tab'
        tmp_value[0][3] = 'asgn'
    else:
        raise Exception("Can't change value to assign")

    return tmp_value

def change_expr_cond_reference(value):
    tmp_value = copy.deepcopy(value)

    if len(tmp_value) == 0:
        return []

    for i in range(len(tmp_value)):
        if tmp_value[i][0] == 'id':
            tmp_value[i][3] = 'ref'
        elif tmp_value[i][0] == 'tab_id':
            tmp_value[i][3] = 'ref'
        elif tmp_value[i][0] == 'tab_num':
            tmp_value[i][3] = 'ref'
        else:
            raise Exception("Can't change value to expr_cond_reference")

    return tmp_value

def change_value_reference(value):
    tmp_value = copy.deepcopy(value)

    if len(tmp_value) == 0:
        return []

    if tmp_value[0][0] == 'id':
        tmp_value[0][3] = 'ref'
    elif tmp_value[0][0] == 'tab_id':
        tmp_value[0][3] = 'ref'
        tmp_value[1][3] = 'ref'
    elif tmp_value[0][0] == 'tab_num':
        tmp_value[0][3] = 'ref'
    else:
        raise Exception("Can't change value to reference")

    return tmp_value

def check_inits(ops_list):
    global declared
    var_usages = {}

    for op in ops_list:
        var_type, var_id, lex_num, op_type = op[0], op[1], op[2], op[3]

        if var_type == 'id':
            if var_id not in var_usages.keys():
                var_usages[var_id] = []

            var_usages[var_id].append([op_type, lex_num])
        elif var_type == 'tab' or var_type == 'tab_id' or var_type == 'tab_num':
            var_id = var_id
            if var_id not in var_usages.keys():
                var_usages[var_id] = []

            var_usages[var_id].append([op_type, lex_num])
        else:
            raise Exception("Can't recognize id/tab type")

    for var_name in var_usages.keys():
        var_usage_list = var_usages[var_name]
        var_usage_list = sorted(var_usage_list, key=lambda usage: usage[1])

        if var_usage_list[0][0] != 'asgn':
            error_log.append('Possibility of variable "{}" being not initialized'.format(var_name))

    declared = sorted(declared)
    double_declared = []

    for var_name in declared:
        if declared.count(var_name) > 1:
            double_declared.append(var_name)

    for var_name in list(set(double_declared)):
        error_log.append('Possibility of variable "{}" being declared more than one time'.format(var_name))

    vars_used_in_code = var_usages.keys()
    vars_used_in_code = [var for var in vars_used_in_code if '@iter' not in var]

    not_declared_vars = list(set(vars_used_in_code).difference(set(declared)))
    for var_name in not_declared_vars:
        error_log.append('Possibility of variable "{}" being not declared and used in code'.format(var_name))


# ######## PARSER ########

def p_program_with_declarations(p):
    """program : DECLARE declarations BEGIN commands END"""
    check_inits(p[4])

def p_program_without_declarations(p):
    """program : BEGIN commands END"""
    check_inits(p[2])

def p_declarations_commasep_single(p):
    """declarations : declarations COMMA ID"""
    declared.append(p[3])

def p_declarations_commasep_array(p):
    """declarations : declarations COMMA ID LBR NUM COLON NUM RBR"""
    if int(p[5]) > int(p[7]):
        error_log.append('Wrong numbers range in array {}'.format(p[3]))
    declared.append(p[3] + '@tab')

def p_declarations_single(p):
    """declarations : ID"""
    declared.append(p[1])

def p_declarations_array(p):
    """declarations : ID LBR NUM COLON NUM RBR"""
    declared.append(p[1] + '@tab')

def p_commands_many(p):
    """commands : commands command"""
    p[0] = p[1] + p[2]

def p_commands_single(p):
    """commands : command"""
    p[0] = p[1]

def p_command_assign(p):
    """command : identifier ASSIGN expression SEMICOLON"""
    ids_list = []
    ids_list += change_value_assign(p[1])
    ids_list += change_expr_cond_reference(p[3])
    p[0] = ids_list

def p_command_if_then_else(p):
    """command : IF condition THEN commands ELSE commands ENDIF"""
    ids_list = []
    ids_list += change_expr_cond_reference(p[2])
    ids_list += p[4]
    ids_list += p[6]
    p[0] = ids_list

def p_command_if_then(p):
    """command : IF condition THEN commands ENDIF"""
    ids_list = []
    ids_list += change_expr_cond_reference(p[2])
    ids_list += p[4]
    p[0] = ids_list

def p_command_while_do(p):
    """command : WHILE condition DO commands ENDWHILE"""
    ids_list = []
    ids_list += change_expr_cond_reference(p[2])
    ids_list += p[4]
    p[0] = ids_list

def p_command_do_while(p):
    """command : DO commands WHILE condition ENDDO"""
    ids_list = []
    ids_list += p[2]
    ids_list += change_expr_cond_reference(p[4])
    p[0] = ids_list

def p_iterator(p):
    '''iterator	: ID '''
    p[0] = p[1]

def p_command_for_to(p):
    """command : FOR iterator FROM value TO value DO commands ENDFOR"""
    global iter_num
    iter_name = p[2] + '@iter' + str(iter_num)
    iter_num += 1

    ids_list = []
    ids_list += change_value_assign([["id", p[2], p.__dict__['slice'][1].__dict__['lexpos'], None]])
    ids_list += change_value_reference(p[4])
    ids_list += change_value_reference(p[6])
    ids_list += p[8]

    for id in p[8]:
        if '@iter' in id[1] and id[1][:-6] == p[2]:
            error_log.append('Nested iterator error: "{}"'.format(p[2]))

    for i in range(len(ids_list)):
        if ids_list[i][1] == p[2]:
            ids_list[i][1] = iter_name

    p[0] = ids_list

def p_command_for_downto(p):
    """command : FOR iterator FROM value DOWNTO value DO commands ENDFOR"""
    global iter_num
    iter_name = p[2] + '@iter' + str(iter_num)
    iter_num += 1

    ids_list = []
    ids_list += change_value_assign([["id", p[2], p.__dict__['slice'][1].__dict__['lexpos'], None]])
    ids_list += change_value_reference(p[4])
    ids_list += change_value_reference(p[6])
    ids_list += p[8]

    for id in p[8]:
        if '@iter' in id[1] and id[1][:-6] == p[2]:
            error_log.append('Nested iterator error: "{}"'.format(p[2]))

    for i in range(len(ids_list)):
        if ids_list[i][1] == p[2]:
            ids_list[i][1] = iter_name

    p[0] = ids_list

def p_command_read(p):
    """command : READ identifier SEMICOLON"""
    ids_list = []
    ids_list += change_value_assign(p[2])
    p[0] = ids_list

def p_command_write(p):
    """command : WRITE value SEMICOLON"""
    ids_list = []
    ids_list += change_value_reference(p[2])
    p[0] = ids_list

def p_expression_val(p):
    """expression : value"""
    p[0] = p[1]

def p_expression_val_plus(p):
    """expression : value PLUS value"""
    p[0] = p[1] + p[3]

def p_expression_val_minus(p):
    """expression : value MINUS value"""
    p[0] = p[1] + p[3]

def p_expression_val_times(p):
    """expression : value TIMES value"""
    p[0] = p[1] + p[3]

def p_expression_val_div(p):
    """expression : value DIV value"""
    p[0] = p[1] + p[3]

def p_expression_val_mod(p):
    """expression : value MOD value"""
    p[0] = p[1] + p[3]

def p_condition_val_eq(p):
    """condition : value EQ value"""
    p[0] = p[1] + p[3]

def p_condition_val_neq(p):
    """condition : value NEQ value"""
    p[0] = p[1] + p[3]

def p_condition_val_le(p):
    """condition : value LE value"""
    p[0] = p[1] + p[3]

def p_condition_val_ge(p):
    """condition : value GE value"""
    p[0] = p[1] + p[3]

def p_condition_val_leq(p):
    """condition : value LEQ value"""
    p[0] = p[1] + p[3]

def p_condition_val_geq(p):
    """condition : value GEQ value"""
    p[0] = p[1] + p[3]

def p_value_num(p):
    """value : NUM"""
    p[0] = []

def p_value_id(p):
    """value : identifier"""
    p[0] = p[1]

def p_identifier_id(p):
    """identifier : ID"""
    p[0] = [
        ["id", p[1], p.__dict__['slice'][1].__dict__['lexpos'], None]
    ]

def p_identifier_id_of_id(p):
    """identifier : ID LBR ID RBR"""
    p[0] = [
        ["tab_id", p[1] + '@tab', p.__dict__['slice'][1].__dict__['lexpos'], None],
        ["id", p[3], p.__dict__['slice'][3].__dict__['lexpos'], None]
    ]

def p_identifier_id_of_num(p):
    """identifier : ID LBR NUM RBR"""
    p[0] = [
        ["tab_num", p[1] + '@tab', p.__dict__['slice'][1].__dict__['lexpos'], None],
    ]

def p_error(p):
    print(p)
    sys.exit("error sys.exit")

def get_error_log(imp_file_path):
    parser = yacc.yacc()
    with open(imp_file_path, 'r') as f:
        code_dev = f.read()
        parser.parse(code_dev)

    return error_log