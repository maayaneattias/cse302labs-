from tac2x64 import compile_tac
from bx2tac import bx_to_tac_json
import sys
import subprocess
import argparse


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Codegen: BX (JSON) to ASM (x64)')
    ap.add_argument('--keep-tac', dest='keep_tac', action='store_true', default=False,
                    help='Produce intermediate tac.json file')
    ap.add_argument('--run', dest='run', action='store_true', default=False,
                    help='Run exe file')
    ap.add_argument('fname', metavar='FILE', type=str, nargs=1,
                    help='The BX(JSON) file to process')
    opts = ap.parse_args(sys.argv[1:])
    fname = opts.fname[0]
    tac = bx_to_tac_json(fname)
    asm = compile_tac(tac)

    # print("ASM:")
    # for i in asm:
    #    print(i)

    cmd = ['gcc', '-o', fname[:-3], 'bx_runtime.c', fname[:-3] + '.s']
    p = subprocess.Popen(cmd)
    p.wait()
    cmd = ['rm', fname[:-3] + '.s']
    #p = subprocess.Popen(cmd)
    p.wait()

    if False and not opts.keep_tac:  
        cmd = ['rm', fname[:-3] + '.tac.json']
        p = subprocess.Popen(cmd)
        p.wait()

    if opts.run:
        cmd = [f"./{fname[:-3]}"]
        p = subprocess.Popen(cmd)
        p.wait()
