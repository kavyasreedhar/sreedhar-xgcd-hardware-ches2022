def print_debug(debug_print, *args):
    if debug_print:
        string = ""
        for arg in args:
            string += str(arg) + " "
        print(string)
