#I chose the BMM implementation so I copy when a variable is written

import auxiliary
import json
import sys

input_file = sys.argv[1]

with open(input_file, 'r') as file:
    js_obj = json.load(file)
    ast = js_obj['ast']
    blocks_list = ast[0][0][0][4][0][1]

    reg_counter = 0 
    var_to_register = {} #{variable name: register} 
    instruction_list_for_body = [] #body is a list of dictionnary encoding instructions

    for block in blocks_list:

        if block[0][0] == "<assign>":
            var = block[0][1][0][1]
            expr = block[0][2][0]
            instruction_list_for_body, reg_counter, register = auxiliary.read_expressions(
                expr, var_to_register, reg_counter, instruction_list_for_body)

            instruction_list_for_body.append(
                {"opcode": "copy", "args": ["%{}".format(register)], "result": "%{}".format(var_to_register[var])})


        if block[0][0] == "<eval>":
            expr = block[0][1][0][2][0][0]
            instruction_list_for_body, reg_counter, register = auxiliary.read_expressions(
                expr, var_to_register, reg_counter, instruction_list_for_body)

            instruction_list_for_body.append(
                {"opcode": "print", "args": ["%{}".format(register)], "result": None})

        if block[0][0] == "<vardecl>":
            #variable declaration always set to const 0
            instruction_list_for_body.append({"opcode": "const", "args": [
                                0], "result": "%{}".format(reg_counter)})
            temp_register = reg_counter
            reg_counter += 1
            var, reg_counter = auxiliary.declare_variables(block[0][1][0], block[0][2][0], reg_counter)
            var_to_register[var.name] = var.register
            instruction_list_for_body.append(
                {"opcode": "copy", "args": ["%{}".format(temp_register)], "result": "%{}".format(var.register)})




output_file = input_file.strip(".json")
output_file += ".tac.json"
output_file = open(output_file, "w")
output_file.write('[ { "proc": "@main", "body": [\n')

for e in instruction_list_for_body[:-1]:
    json.dump(e, output_file)
    output_file.write(",\n")
json.dump(instruction_list_for_body[-1], output_file)
output_file.write("\n")
output_file.write("]}]")
output_file.close()
