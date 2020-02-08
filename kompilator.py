import compiler_checker
import compiler_parser
import sys


def run_compiler(imp_input_path, mr_output_path):
    errors = []

    try:
        errors = compiler_checker.get_error_log(imp_input_path)
    except:
        pass

    for err in errors:
        sys.stderr.write(err + '\n')

    try:
        compiler_parser.parse_file(imp_input_path, mr_output_path)
    except:
        print('Compiling failed')

if __name__ == "__main__":
    if len(sys.argv) == 3:
        run_compiler(sys.argv[1], sys.argv[2])