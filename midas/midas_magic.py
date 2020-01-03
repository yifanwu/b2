from IPython import get_ipython # type: ignore
from IPython.core.magic import (Magics, magics_class, line_magic, cell_magic, line_cell_magic)  # type: ignore
from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)  # type: ignore

from .ui_comm import UiComm

@magics_class
class MidasMagic(Magics):
    ui_comm: UiComm
    def __init__(self, shell, ui_comm: UiComm):
        super(MidasMagic, self).__init__(shell)
        self.ui_comm = ui_comm

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
            # self.ui_comm.send_debug_msg(f"NEW cell magic with shell: { args.df_name} with cell: {cell}")
            self.ui_comm.add_reactive_cell(args.df_name)
            shell = get_ipython().get_ipython()
            shell.run_cell(cell)
        else:
            print("\x1b[31mYou need to call %%reactive with the name of the chart. This cell is not exeucted\x1b[0m")

# def execute_cell(cell):
#     shell = get_ipython().get_ipython()
#     r =  shell.run_cell(cell)
#     if r.error_in_exec:
#         return r.error_in_exec
#     else:
#         return r.result
