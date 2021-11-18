import tac
import cfg
import ssagen
import sys
import argparse
import json


if __name__ == '__main__':
    # change this for the -o when taking into account saving to file
    #ap = argparse.ArgumentParser()
    #ap.add_argument('-o', dest='o', action='store_true', default=False)
    #opts = ap.parse_args(sys.argv[1:])

    # Gvars and Procs generation from input file
    gvars, procs = dict(), dict()
    for decl in tac.load_tac(sys.argv[-1]):
        if isinstance(decl, tac.Gvar):
            gvars[decl.name] = decl
        else:
            procs[decl.name] = decl

    print("First: ")
    tac.execute(gvars, procs, '@main', [])
    print("First done")

    # CFG Generation from procs
    CFGs = dict()
    for name, proc in procs.items():
        CFGs[name] = cfg.infer(proc)

    # DSE
    for name, CFG in CFGs.items():
        change = True
        while change == True:
            change = False

            livein, liveout = dict(), dict()
            cfg.recompute_liveness(CFG, livein, liveout)
            for instr in CFG.instrs():
                if instr.opcode in ['div', 'mod', 'call'] or instr.dest in gvars.keys() or instr.arg1 in gvars.keys() or instr.arg2 in gvars.keys():
                    continue
                elif instr.dest != None and (instr.dest not in liveout[instr]):
                    change = True
                    # delete dead store instr
                    for block in CFG._blockmap.values():
                        if instr in block.body:
                            block.body.remove(instr)
                            break

    # SSA Generation from procs and cfgs
    for name in CFGs:
        ssagen.crude_ssagen(procs[name], CFGs[name])

    # GCP
    for name, CFG in CFGs.items():
        for instr in CFG.instrs():
            if instr.opcode == 'copy' and instr.dest not in gvars.keys() and instr.arg1 not in gvars.keys():
                find = instr.dest  # to replace everywhere by replace
                replace = instr.arg1
                deleted = False
                for block in CFG._blockmap.values():
                    # delete copy instr
                    if instr in block.body and deleted == False:
                        deleted = True
                        block.body.remove(instr)
                    #find and replace
                    for temp_instr in block.body:
                        if (temp_instr.dest in gvars.keys()):
                            continue
                        if temp_instr.opcode == "phi":
                            for (k, v) in temp_instr.arg1.items():
                                if v in gvars.keys():
                                    continue
                                elif v == find:
                                    temp_instr.arg1[k] = replace
                        else:
                            if temp_instr.arg1 == find and temp_instr.arg1 not in gvars.keys():
                                temp_instr.arg1 = replace
                            if temp_instr.arg2 == find and temp_instr.arg2 not in gvars.keys():
                                temp_instr.arg2 = replace

    # linearize back from CFG to procs
    for name, CFG in CFGs.items():
        cfg.linearize(procs[name], CFG)

    # printing the TAC or outputing it into a file

    accumulated = []
    for decl in gvars.values():
        accumulated.append(decl)
    for decl in procs.values():
        accumulated.append(decl)
    if len(sys.argv) == 2:
        for obj in accumulated:
            print(obj)
    elif len(sys.argv) == 4 and sys.argv[1] == "-o":
        with open(sys.argv[2], 'w') as tac_file:
            json.dump(accumulated, tac_file)
    else:
        raise ValueError(
            "You should either provide only 1 argument (a file name), or -o followed with 2 filenames (input and output)!")

    print("Second: ")
    tac.execute(gvars, procs, '@main', [])
    print("Second done")
