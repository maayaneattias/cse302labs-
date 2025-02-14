from bx2tac import Instr, GlobalVar, Proc

import sys
import json


class BasicBlock:
    def __init__(self, instrs):
        self.label = instrs[0].args[0]
        self.instrs = instrs  # [Instr, Instr,...]
        self.predecessor = set()
        self.successor = set()

    def add_predecessor(self, parent_label):
        self.predecessor.add(parent_label)

    def add_successor(self, kid_label):
        self.successor.add(kid_label)

    def __repr__(self):
        return "Label: {} ; Instructions: {}".format(self.label, self.instrs)

    def absorb(self, block):
        self.instrs += block.instrs
        for kid_label in block.successor:
            self.successor.add(kid_label)


class CFG:
    def __init__(self, instructions, proc_name):
        self.name = proc_name[1:]
        self.block_inference(instructions)

    def block_inference(self, instructions):
        self.blocks = dict()  # = {block_label : block_instance, ...}

        # Step 1: Add an entry label before first instruction if needed.
        if instructions[0].opcode != 'label':
            entry_label = f'.Lentry_{self.name}'
            new_instruction = Instr('label', [entry_label], None)
            instructions.insert(0, new_instruction)
            self.initial_block_label = entry_label
        else:
            self.initial_block_label = instructions[0].args[0]

        cond_jumps = ['jz', 'jnz', 'jl', 'jle', 'jg', 'jge', 'jnl', 'jnle']
        count_label = 0
        to_add = []
        for i in range(len(instructions)):
            if instructions[i].opcode == 'jmp':
                # Step 2: For jumps,add a label after the instruction if one doesn’t already exist.
                if (i < len(instructions)-1 and instructions[i+1].opcode != 'label'):
                    count_label += 1
                    new_label = f".Ljmp_{self.name}_{count_label}"
                    to_add.append((i+1, Instr('label', [new_label], None)))

            # Step 4: Add explicit jmps for fall-throughs
            if i >= 1 and instructions[i].opcode == 'label' and instructions[i-1].opcode != 'jmp':
                new_instruction = Instr('jmp', [instructions[i].args[0]], None)
                to_add.append((i, new_instruction))

            # WHEN THERE IS NOTHING TO RETURN, WE RETURN THIS
            # remove
            if i == len(instructions)-1 and instructions[i].opcode != 'jmp' and instructions[i].opcode != 'ret':
                new_instruction = Instr('ret', [], None)
                to_add.append((i+1, new_instruction))

        #print("TO ADD!!!")
        # print(to_add)
        for i in range(len(to_add)):
            (index, instruction) = to_add[i]
            instructions.insert(index+i, instruction)

        # Step 3: Start a new block at each label
        block_instr = []
        edges = []  # [(parent, kid)]
        for i in range(len(instructions)):
            block_instr.append(instructions[i])
            if instructions[i].opcode == 'jmp':
                # block until jmp instruction built
                new_block = BasicBlock(block_instr)
                self.blocks[new_block.label] = new_block
                destination_label = instructions[i].args[0]
                edges.append((new_block.label, destination_label))
                block_instr = []
            elif instructions[i].opcode == 'ret':
                new_block = BasicBlock(block_instr)
                self.blocks[new_block.label] = new_block
                block_instr = []
            elif instructions[i].opcode in cond_jumps:
                origin_label = block_instr[0].args[0]
                destination_label = instructions[i].args[1]
                edges.append((origin_label, destination_label))

        # print("BLOCKS!")
        # print(self.blocks.values())
        # print("edges")
        # print(edges)

        for (parent, kid) in edges:
            self.blocks[parent].add_successor(kid)
            self.blocks[kid].add_predecessor(parent)

        print("CFG was successfully built")

    def serialize(self, final=True):
        initial_block = self.blocks[self.initial_block_label]
        serialized_instrs = initial_block.instrs  # list of instructions
        serialized_block_labels = set([self.initial_block_label])

        def UCE(block):
            # serializing only successors of blocks so we eliminate unreachable blocks
            for kid_label in block.successor:
                if kid_label not in serialized_block_labels:
                    kid_block = self.blocks[kid_label]
                    serialized_instrs.extend(kid_block.instrs)
                    serialized_block_labels.add(kid_label)
                    UCE(kid_block)

        UCE(initial_block)

        if final:
            # then Fall-Through Simplification
            useless_jmps = []
            for index in range(len(serialized_instrs)-1):
                current_instr = serialized_instrs[index]
                if current_instr.opcode == 'jmp':
                    next_instr = serialized_instrs[index+1]
                    if next_instr.opcode == 'label' and next_instr.args[0] == current_instr.args[0]:
                        useless_jmps.append(index)  # delete jmp instruction

            if len(useless_jmps) >= 1:
                useless_jmps.reverse()
                for index in useless_jmps:
                    serialized_instrs.pop(index)

        return serialized_instrs

    def coalesce(self):
        old_block_label = None
        for block in list(self.blocks.values()):
            # Check if block has only one kid
            if len(block.successor) == 1:
                kid_block_label = list(block.successor)[0]
                kid_block = self.blocks[kid_block_label]
                # Check if kid_block has only one parent and if kid_block is not the inital block
                if len(kid_block.predecessor) == 1 and kid_block_label != self.initial_block_label:
                    # Check if last instruction of the parent block is jmp
                    if block.instrs[-1].instr.opcode == 'jmp':
                        # Kill jmp instruction at the end of absorbing block
                        block.instrs[-1].instr.opcode = 'nop'
                        # Absorb kid_block into block
                        block.absorb(kid_block)
                        # Prepare kid_block name for deletion
                        old_block_label = kid_block.label
                        break

        if old_block_label:
            # Delete blocks that have been absorbed
            self.blocks.pop(old_block_label)
            # Remove old_block_label from the kids and parents of all blocks
            for block in self.blocks.values():
                if old_block_label in block.successor:
                    block.successor.remove(old_block_label)
                if old_block_label in block.predecessor:
                    block.predecessor.remove(old_block_label)

            return (block.label, old_block_label)
        else:
            return False

    def unreachable_code_elimination(self):
        serialized_instrs = self.serialize(False)  # remove unreachable blocks
        # print("serialized_instrs!!!")
        # print(serialized_instrs)
        self.block_inference(serialized_instrs)  # build cfg again

    def jump_thread(self):
        """
        -Jump threading for unconditional jump sequences
        -Jump threading to turn conditional jumps into unconditional jumps
        """

        def build_linear_seq(block, linear_seq_so_far):
            if len(block.successor) == 1:
                kid_block_label = list(block.successor)[0]
                kid_block = self.blocks[kid_block_label]
                if len(kid_block.predecessor) == 1:
                    linear_seq_so_far += [kid_block_label]
                    return build_linear_seq(kid_block, linear_seq_so_far)
            return linear_seq_so_far

        old_block_labels = set()

        for block_label, block in self.blocks.items():

            # Unconditional Jumps ----------------------------------------------

            # Generate a linear sequence of blocks
            linear_seq_of_block_labels = build_linear_seq(
                block, [block_label])[:-1]
            if len(linear_seq_of_block_labels) > 1:
                for i in range(1, len(linear_seq_of_block_labels)-1):
                    body = self.blocks[linear_seq_of_block_labels[i]
                                       ].instrs[1:-1]
                    # Proceed only if all blocks in the sequnce have empty bodies
                    if len(body) != 0:
                        break
                else:
                    # Change jump instruction in the first block to go to the last block
                    first_block = self.blocks[linear_seq_of_block_labels[0]]
                    first_block.instrs[-1].args[0] = linear_seq_of_block_labels[-1]
                    # Absorb all blocks into the first block
                    for label in linear_seq_of_block_labels[1:-1]:
                        first_block.absorb(self.blocks[label])
                        # Prepare old blocks for deletion
                        for block_label in linear_seq_of_block_labels[1:-1]:
                            old_block_labels.add(block_label)

            # Conditional Jumps ------------------------------------------------

            for kid_block_label in block.successor:

                # Check if there's a conditional jump in block to kid_block
                tmp = None
                for instr in block.instrs:
                    if instr.opcode in {'jz', 'jnz', 'jl', 'jle'} and instr.args[1] == kid_block_label:
                        tmp = instr.args[0]
                        cjmp = instr.opcode
                if not tmp:
                    continue

                # Check if the tmp is unchnaged in kid_block
                changed = False
                kid_block = self.blocks[kid_block_label]
                for instr in kid_block.instrs:
                    if instr.result == tmp:
                        changed = True
                        break
                if changed:
                    continue

                # Check if a same conditional jump with the same tmp exists in kid_block
                for i in range(len(kid_block.instrs) - 1):
                    if kid_block.instrs[i].opcode == cjmp and kid_block.instrs[i].args[0] == tmp:
                        next_label = kid_block.instrs[i].args[1]
                        # Kill the conditional jump
                        kid_block.instrs[i].opcode = 'nop'
                        if kid_block.instrs[i+1].opcode == 'jmp':
                            # Change the label of the next jump
                            kid_block.instrs[i+1].args[0] = next_label

        # Delete blocks that have been absorbed
        for old_block_label in old_block_labels:
            self.blocks.pop(old_block_label, None)

    def optimize(self):
        """Perform some simple control flow optimizations in order: 
        -Jump threading
        -Unreachable code elimination(UCE): should be run after every other simplification, particularly jump threading.
        -coalesce: perform one round of coalescing after every other CFG simplification phase.
        """

        self.jump_thread()
        print("Jump thread done")
        self.unreachable_code_elimination()
        print("UCE done")
        coalesced_blocks = set()
        while True:
            coalescing = self.coalesce()
            self.unreachable_code_elimination()
            if coalescing != False and coalescing not in coalesced_blocks:
                coalesced_blocks.add(coalescing)  # add (B1,B2)
            else:
                break
        print("Coalesced done")


def optimization(filename):
    # check it's correct
    gvars = []
    procs = []
    print(f'[[ Optimizing {filename} ]]')

    with open(filename, 'rb') as fp:
        tjs = json.load(fp)
    assert isinstance(tjs, list), tjs

    # Global Variables
    for decl in tjs:
        if 'var' in decl:
            gvars.append(decl)

    # Procedure Control Flow Optimization
    for decl in tjs:
        if 'proc' in decl:
            name = decl['proc']
            args = decl['args']
            body = decl['body']
            tac_instructions = []
            for dico in body:
                tac_instructions.append(
                    Instr(dico["opcode"], dico["args"], dico["result"]))
            print(f"Building CFG for {name}")
            cfg = CFG(tac_instructions, name)
            print(f"Optimization for {name}")
            cfg.optimize()
            print(f"Serialization for {name}")
            proc_instrs = cfg.serialize()
            body = []
            for instr in proc_instrs:
                body.append(instr.js_obj)
            procs.append({"proc": name, "args": args, "body": body})

    # Write to file
    print("Optimization done - Writing file")
    full = gvars+procs
    with open(f'{filename[:-9]}.optimized_tac.json', 'w') as tac_file:
        json.dump(full, tac_file)

    # for decl in full:
    #     print(decl)

    print(f'[[ Output {filename[:-9]}.optimized_tac.json ]]')
    tac_name = f'{filename[:-9]}.optimized_tac.json'
    return tac_name


if __name__ == "__main__":
    # is there a way to access the object directly from the json file loaded without creating again

    for filename in sys.argv[1:]:
        gvars = []
        procs = []
        print(f'[[ Optimizing {filename} ]]')

        with open(filename, 'rb') as fp:
            tjs = json.load(fp)

        assert isinstance(tjs, list), tjs

        # Global Variables
        for decl in tjs:
            if 'var' in decl:
                gvars.append(decl)

        # Procedure Control Flow Optimization
        for decl in tjs:
            if 'proc' in decl:
                name = decl['proc']
                args = decl['args']
                body = decl['body']
                tac_instructions = []
                for dico in body:
                    tac_instructions.append(
                        Instr(dico["opcode"], dico["args"], dico["result"]))
                print(f"Building CFG for {name}")
                cfg = CFG(tac_instructions, name)
                print(f"Optimization for {name}")
                cfg.optimize()
                print(f"Serialization for {name}")
                proc_instrs = cfg.serialize()
                body = []
                for instr in proc_instrs:
                    body.append(instr.js_obj)
                procs.append({"proc": name, "args": args, "body": body})

        # Write to file
        print("Optimization done - Writing file")
        full = gvars+procs
        with open(f'{filename[:-9]}.optimized_tac.json', 'w') as tac_file:
            json.dump(full, tac_file)

        for decl in full:
            print(decl)

        print(f'[[ Output {filename[:-9]}.optimized_tac.json ]]')

# in bxcc should we use bxtotac but does not output the json but directly the tac_prgram with the object?
# so we don't need to convert in tac_cfopt and tac_to_asm
# we load the tac (parse and scan) and then use directly the object
