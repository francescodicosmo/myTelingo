"""
The telingo module contains functions to translate and solve temporal logic
programs.
"""

import sys
import clingo
import telingo.transformers as transformers
from textwrap import dedent

def imain(prg, future_sigs, program_parts, on_model, imin = 0, imax = None, istop = "SAT"):
    """
    Take a program object and runs the incremental main solving loop.

    For each pair (name, arity) in future_sigs all atoms in the program base
    with the time parameter referring to the future are set to false. For
    example, given (p, 2) and atoms  p(x,1) in step 0, the atom would p(x,1)
    would be set to false via an assumption. In the following time steps, it
    would not be set to False.

    The list program_parts contains all program parts appearing in the program
    in form of triples (root, name, range) where root is either "initial" (time
    step 0), "static" (time steps >= 0), or "dynamic" (time steps > 0) and
    range is a list of integers for which the part has to be grounded
    backwards. Given range [0, 1] and root "static", at each iteration the
    program part would be grounded at horizon and horizon-1. The latter only if
    the horizon is greater than 0.

    Arguments:
    prg           -- Control object holding the program.
    future_sigs   -- Signatures of predicates whose future incarnations have to
                     be set to False.
    program_parts -- Program parts to ground.
    imin          -- Minimum number of iterations.
    imax          -- Maximum number of iterations.
    istop         -- When to stop.
    """
    step, ret = 0, None
    while ((imax is None or step < imax) and
           (step == 0 or step < imin or (
              (istop == "SAT"     and not ret.satisfiable) or
              (istop == "UNSAT"   and not ret.unsatisfiable) or
              (istop == "UNKNOWN" and not ret.unknown)))):
        parts = []
        for root_name, part_name, rng in program_parts:
            for i in rng:
                if ((step - i >= 0 and root_name == "static") or
                    (step - i  > 0 and root_name == "dynamic") or
                    (step - i == 0 and root_name == "initial")):
                    parts.append((part_name, [step - i, step]))
        if step > 0:
            prg.release_external(clingo.Function("__final", [step-1]))
            prg.cleanup()

        prg.ground(parts)
        prg.assign_external(clingo.Function("__final", [step]), True)
        assumptions = []
        for name, arity in future_sigs:
            for atom in prg.symbolic_atoms.by_signature(name, arity):
                if atom.symbol.arguments[-1].number > step:
                    assumptions.append(-atom.literal)
        ret, step = prg.solve(on_model=lambda m: on_model(m, step), assumptions=assumptions), step+1

class Application:
    """
    Application object as accepted by clingo.clingo_main().

    Rewrites the incoming temporal logic programs into incremental ASP programs
    and solves them.
    """
    def __init__(self, name):
        """
        Initializes the application setting the program name.

        See clingo.clingo_main().
        """
        self.program_name = name
        self.__imin = 0
        self.__imax = None
        self.__istop = "SAT"

    def __on_model(self, model, steps):
        """
        Prints the atoms in a model grouped by state.

        Arguments:
        model -- The model to print.
        steps -- The number of states.
        """
        table = {}
        for sym in model.symbols(shown=True):
            if sym.type == clingo.SymbolType.Function and len(sym.arguments) > 0:
                table.setdefault(sym.arguments[-1].number, []).append(clingo.Function(sym.name, sym.arguments[:-1]))
        sys.stdout.write("Answer: {}\n".format(model.number))
        for step in range(steps+1):
            symbols = table.get(step, [])
            sys.stdout.write(" State {}:".format(step))
            sig = None
            for sym in sorted(symbols):
                if not sym.name.startswith('__'):
                    if (sym.name, len(sym.arguments)) != sig:
                        sys.stdout.write("\n ")
                        sig = (sym.name, len(sym.arguments))
                    sys.stdout.write(" {}".format(sym))
            sys.stdout.write("\n".format(step))
        return True

    def __parse_imin(self, value):
        """
        Parse imin argument.
        """
        self.__imin = int(value)
        return self.__imin >= 0

    def __parse_imax(self, value):
        """
        Parse imax argument.
        """
        self.__imax = int(value)
        return self.__imax >= 0

    def __parse_istop(self, value):
        """
        Parse istop argument.
        """
        self.__istop = value.upper()
        return self.__istop in ["SAT", "UNSAT", "UNKNOWN"]

    def register_options(self, options):
        """
        See clingo.clingo_main().
        """
        group = "Telingo Options"
        options.add(group, "imin", "Minimum number of solving steps [0]", self.__parse_imin, argument="<n>")
        options.add(group, "imax", "Maximum number of solving steps", self.__parse_imax, argument="<n>")
        options.add(group, "istop", dedent("""\
            Stop criterion [sat]
                  <arg>: {sat|unsat|unknown}"""), self.__parse_istop)

    def main(self, prg, files):
        """
        Implements the incremental solving loop.

        This function implements the Application.main() function as required by
        clingo.clingo_main().
        """
        with prg.builder() as b:
            files = [open(f) for f in files]
            if len(files) == 0:
                files.append(sys.stdin)
            future_sigs, program_parts = transformers.transform([f.read() for f in files], b.add)

        imain(prg, future_sigs, program_parts, self.__on_model, self.__imin, self.__imax, self.__istop)

def main():
    """
    TODO: it would be cool if it where possible to replace part of the output
    """
    ret = clingo.clingo_main(Application(sys.argv[0]), ["-q2"] + sys.argv[1:])
    sys.exit(int(ret))
