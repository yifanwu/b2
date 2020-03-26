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
    @argument('-disable', action="store_true", help="disable this reactive cell")
    @argument('-df', action='store', help='the name of the df, do not set this flag if you wish the cell to be ran for all interactions')
    # add another argument such that they can use append based
    # @argument('--append', action="store")
    def reactive(self, line: str, cell: str):
        args = parse_argstring(self.reactive, line)
        # do_append = "append" in args
        if args.disable:
            # self.ui_comm.send_debug_msg("disabled")
            self.ui_comm.remove_reactive_cell()
            # do NOT execute the cell
            return
        if args.df:
            # self.ui_comm.send_debug_msg(f"NEW cell magic with shell: {args.df} with cell: {cell}")
            self.ui_comm.add_reactive_cell(args.df)
        else:
            self.ui_comm.add_reactive_cell("")
            
        shell = get_ipython().get_ipython()
        shell.run_cell(cell)