# extracting out the magic part for better testing...

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
@magics_class
class MidasMagic(Magics):

    def __init__(self, shell, midas):
        super(MidasMagic, self).__init__(shell)
        self.midas = midas


    @cell_magic
    def reactive(self, df_name: str, line, cell=None):
        """react_to is a cell or line magic (based on how many '%' were specified)
        
        Arguments:
            df_name {str} -- the visualization whose 
        """
        # for now, just do a regex for what df_names are mentioned
        # and re-run the cell
    @cell_magic
    def test(self, line: str, cell: str):
        print("cell", cell)
        print("line", line)
        print("executing with shell with import")
        # exec(cell)
        # hack
        with_import = "import pandas as pd\n"+cell
        # shell = get_ipython().get_ipython()
        # shell.run_cell(with_import)
        exec(with_import)

    @cell_magic
    def state(self, line: str, cell: str):
        if hasattr(self, 'k'):
            self.k += 1
            print(self.k)
        else:
            self.k = 1
            print(self.k)

