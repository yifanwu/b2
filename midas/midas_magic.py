# extracting out the magic part for better testing...
from IPython import get_ipython
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython.core.magic_arguments import (argument, magic_arguments,
    parse_argstring)

@magics_class
class MidasMagic(Magics):

    def __init__(self, shell, comm):
        super(MidasMagic, self).__init__(shell)
        self.comm = comm


    @cell_magic
    @magic_arguments()
    # @argument('-o', '--option', help=An optional argument.')
    @argument('df_name', type=str, help='the name of the chart/dataframe')
    def reactive(self, line: str, cell: str):
        """react_to is a cell or line magic (based on how many '%' were specified)
        
        Arguments:
            df_name {str} -- the visualization whose 
        """
        args = parse_argstring(self.reactive, line)
        if (args.df_name):
            print("NEW cell magic with shell", args.df_name, "with cell", cell)
            self.comm.send({"type": "reactive", "value": args.df_name})
            shell = get_ipython().get_ipython()
            shell.run_cell(cell)
        else:
            print("\x1b[31mYou need to call %%reactive with the name of the chart. This cell is not exeucted\x1b[0m")


    @cell_magic
    def test(self, line: str, cell: str):
        shell = get_ipython().get_ipython()
        shell.run_cell(cell)
        # if r.error_in_exec:
        #     r.error_in_exec
        # else:
        #     r.result

    @cell_magic
    def state(self, line: str, cell: str):
        return
    #     if hasattr(self, 'k'):
    #         self.k += 1
    #         print(self.k)
    #     else:
    #         self.k = 1
    #         print(self.k)

def execute_cell(cell):
    shell = get_ipython().get_ipython()
    r =  shell.run_cell(cell)
    if r.error_in_exec:
        return r.error_in_exec
    else:
        return r.result
