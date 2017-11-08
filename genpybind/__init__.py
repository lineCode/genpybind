from __future__ import print_function

import sys
import subprocess
import shutil
import os
import tempfile

from .decls import gather_declarations
from .expose import expose_as

def main():
    import argparse
    import os

    from clang.cindex import TranslationUnit

    parser = argparse.ArgumentParser()

    parser.add_argument("--genpybind-module", dest="module", required=True)
    parser.add_argument("--genpybind-docstring", dest="docstring")
    parser.add_argument("--genpybind-include", nargs="+", dest="includes")
    parser.add_argument("--genpybind-isystem", nargs="+", dest="isystem")
    parser.add_argument("--genpybind-tag", nargs="+", dest="tags")
    parser.add_argument("--genpybind-from-ast", dest="from_ast")
    parser.add_argument("--genpybind-ipython", action="store_true", dest="ipython")
    parser.add_argument('rest', nargs=argparse.REMAINDER)

    # args, rest_args = parser.parse_known_args()
    args = parser.parse_args()

    if args.from_ast:
        if args.rest:
            parser.error(
                "unexpected arguments with --genpybind-from-ast: {}".format(args.rest))
        tu = TranslationUnit.from_ast_file(args.from_ast)
    else:
        name = tempfile.mkdtemp(prefix="genpybind")
        ast_file = os.path.join(name, "genpybind.ast")
        try:
            rest = args.rest[:]
            if rest[0] == "--":
                del rest[0]
            status = subprocess.call(
                ["genpybind-parse", "-output-file", ast_file] + rest, stdout=sys.stderr)
            if status != 0:
                parser.error("genpybind-parse returned status {} when called with\n{}".format(
                    status, rest))
            tu = TranslationUnit.from_ast_file(ast_file)
        finally:
            shutil.rmtree(name)

    if len(tu.diagnostics) != 0:
        for diag in tu.diagnostics:
            print("//", diag.format())
            for diag_ in diag.children:
                print("//", "  ", diag_.format())

    toplevel_declarations = gather_declarations(tu.cursor)

    if args.ipython:
        from IPython import embed
        embed()

    print(expose_as(
        toplevel_declarations,
        module=args.module,
        doc=args.docstring,
        isystem=args.isystem,
        includes=args.includes,
        tags=args.tags,
    ))