from typing import NamedTuple, Callable, List

class JoinInfo(NamedTuple):
    dfs: List[str]
    join_colums: List[str]