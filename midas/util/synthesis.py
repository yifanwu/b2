from pandas import DataFrame
from midas.constants import CUSTOM_INDEX_NAME

# note that this is a temporary hack
def get_df_transform_func_by_join_on_index(target_df: DataFrame):
    # basically add a 
    def transform(df_in: DataFrame):
        import pandas as pd
        return pd.merge(target_df, df_in, how="inner", on=CUSTOM_INDEX_NAME)
    return transform