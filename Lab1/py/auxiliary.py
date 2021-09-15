import expressions
import json

#The functions declare_variables and read_expressions were discussed with my classmate Gorazd dimitrov
#we collaborated and chose their structure and what they should return before each of us wrote the code by itself


bx_to_tac_operations = {"PLUS": "add", "MINUS": "sub", "TIMES": "mul", "DIV": "div", "MODULUS": "mod", "BITAND": "and", "BITOR": "or", "BITXOR": "xor",
              "BITSHL": "shl", "BITSHR": "shr", "UMINUS": "neg", "BITCOMPL": "not"}


def declare_variables(name, value, register_count):
    return (expressions.Variable(name, value, register_count), register_count+1)



def read_expressions(expression, var_to_register, register_count, instruction_list_for_body):
    if expression[0] == '<var>':
        return (instruction_list_for_body, register_count, var_to_register[expression[1]])

    elif expression[0] == '<number>':
        instruction_list_for_body.append({"opcode": "const", "args": [
            expression[1]], "result": "%{}".format(register_count)})
        return instruction_list_for_body, register_count+1, register_count

    elif expression[0] == '<unop>':
        operation = expression[1][0][0]
        instruction_list_for_body, register_count, register = read_expressions(
            expression[2][0], var_to_register, register_count, instruction_list_for_body)
        instruction_list_for_body.append({"opcode": bx_to_tac_operations[operation], "args": ["%{}".format(
            register)], "result": "%{}".format(register_count)})
        return instruction_list_for_body, register_count+1, register_count

    elif expression[0] == '<binop>':
        instruction_list_for_body, register_count, arg1_register = read_expressions(
            expression[1][0], var_to_register, register_count, instruction_list_for_body)
        instruction_list_for_body, register_count, arg2_register = read_expressions(
            expression[3][0], var_to_register, register_count, instruction_list_for_body)
        operation = expression[2][0][0]

        instruction_list_for_body.append({"opcode": bx_to_tac_operations[operation], "args": ["%{}".format(arg1_register), "%{}".format(arg2_register)
                                                                ], "result": "%{}".format(register_count)})
        return instruction_list_for_body, register_count+1, register_count
    
    else:
        print(f'Unrecognized <expr> form: {expression[0]}')
        raise ValueError  
