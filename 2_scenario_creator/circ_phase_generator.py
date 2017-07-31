import sys
import os
import importlib
import inspect
import shutil
import fileinput
import argparse
import re

root_directory = os.path.dirname(os.path.realpath(__file__))
phase_directory = os.path.join(root_directory, "bin/ai_utils/phases")
script_directory = os.path.join(root_directory, "scripts/")

def make_parser():
    """
        Create ArgumentParser object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--phase', required=True,
                        help='A list containing all the desired phase names')
    return parser

def get_inputs(phase):
    """
        Populate list of required and optional arguments
    """

    req_inputs = {}
    opt_inputs = {}

    # Get arguments from __init__ method object
    phase_class = get_class_object(phase)[0][1]
    init_method = None
    for method in inspect.getmembers(phase_class, inspect.ismethod):
        if method[0] == '__init__':
            init_method = method[1]
    args = inspect.getargspec(init_method)

    # inspect.getargspec returns a tuple of four lists - args, varargs, keywords, and defaults
    # If defaults exists set opt_inputs to corresponding arguments with stated defaults and req_inputs to remaining
    # args excluding self and is_phase_critical arguments
    # Otherwise, just set req_inputs to all arguments besides self, and is_phase_critical
    if args[3]:
        for req_arg in args[0][2:len(args[0])-len(args[3])]:
            req_inputs[req_arg] = None

        for opt_arg in zip(reversed(args[0]),reversed(args[3])):
            opt_inputs[opt_arg[0]] = str(opt_arg[1])
    else:
        for req_arg in args[0][2:]:
            req_inputs[req_arg] = None

    return req_inputs, opt_inputs


def get_class_object(phase):
    """
        Returns a class object belonging to the main class of the given phase module
    """
    phase_mod = importlib.import_module(phase)
    phase_mod_classes = inspect.getmembers(phase_mod, inspect.isclass)

    #This line assumes that any non-ai_utils phase imports are entire modules and not specific classes
    phase_mod_classes = filter(lambda (name, obj):
                               'ai_utils' not in str(obj) and name != "AbstractCircadencePhase",
                               phase_mod_classes)

    if len(phase_mod_classes) == 0:
        print("Error in finding class object")
        raise AttributeError

    return phase_mod_classes


def copy_phase(phase, cir_phase_path, init):
    """
        Convert phase to circadence phase
    """

    phase_path = os.path.join(phase_directory, phase + ".py")

    original = open(phase_path, 'r')
    copy = open(cir_phase_path, 'w')

    # TODO: come up with better solution
    # regex subs on each line and write line to file
    for line in original:
        line = re.sub(r"(from )ai_utils.phases.abstract_phase( import )AbstractPhaseClass", r"\1abstract_circadence_phase\2AbstractCircadencePhase", line)
        line = re.sub(r"(\s*class.*)AbstractPhaseClass", r"\1AbstractCircadencePhase", line)
        line = re.sub(r"(\s*def __init__\(self,).*", r"\1info):", line)
        line = re.sub(r"(\s*Abstract)(Phase)Class(.__init__\(self,).*", r"\1Circadence\2\3info=info)\n{}".format(init), line)
        copy.write(line)


def insert_req(phase, cir_phase_path, req_inputs, opt_inputs):
    """
        Put Create function and necessary input paramaters into phase
    """

    for line in fileinput.input(cir_phase_path, inplace=True):
        if re.match(r"^\s*Description.*\n", line):
            print(re.sub(r"(^\s*Description.*\n)",
                       r"\1\n    required_input_parameters = {}"\
                        "\n    optional_input_parameters = {}"\
                        "\n    output_parameters = {}".format(req_inputs,opt_inputs,"{}"), line))
        else:
            sys.stdout.write(line)

    phase_class = get_class_object(phase)[0][0]

    # Append Create
    with open(cir_phase_path,"a") as file:
        file.write('\ndef create(info):\n    """\n        '\
            'Create a new instance of the phase\n    """\n'\
            '\n    return {}(info)\n'.format(phase_class))



def generate_init(req_inputs, opt_inputs):
    init = ""

    for req in req_inputs.keys():
        init += "\t{0} = self.PhaseResult['{0}']\n".format(req)
    for opt in opt_inputs:
        init += "\t{0} = self.PhaseResult['{0}']\n".format(opt)

    return init


def main():

    args = make_parser().parse_args()
    cir_phase_path = os.path.join(script_directory, args.phase + ".py")

    # Gather necessary requirements
    req_inputs, opt_inputs = get_inputs(args.phase)
    init = generate_init(req_inputs,opt_inputs)

    #Generate phase
    copy_phase(args.phase, cir_phase_path, init)
    insert_req(args.phase, cir_phase_path, req_inputs, opt_inputs)


if __name__ == '__main__':

    # Append phase and ai_utils directory to python path
    sys.path.append(os.path.join(root_directory,'./bin/ai_utils/phases'))

    main()