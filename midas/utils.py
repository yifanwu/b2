# taken from https://github.com/vega/ipyvega/blob/master/vega/utils.py
def prepare_spec(spec, data=None):
    """Prepare a Vega-Lite spec for sending to the frontend.

    This allows data to be passed in either as part of the spec
    or separately. If separately, the data is assumed to be a
    pandas DataFrame or object that can be converted to to a DataFrame.

    Note that if data is not None, this modifies spec in-place
    """
    import pandas as pd

    if isinstance(data, pd.DataFrame):
        # We have to do the isinstance test first because we can't
        # compare a DataFrame to None.
        data = sanitize_dataframe(data)
        spec['data'] = {'values': data.to_dict(orient='records')}
    elif data is None:
        # Assume data is within spec & do nothing
        # It may be deep in the spec rather than at the top level
        pass
    else:
        # As a last resort try to pass the data to a DataFrame and use it
        data = pd.DataFrame(data)
        data = sanitize_dataframe(data)
        spec['data'] = {'values': data.to_dict(orient='records')}
    return spec
