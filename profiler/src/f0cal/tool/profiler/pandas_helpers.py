import pandas as pd
import wrapt

def required_columns(cols):
    @wrapt.decorator
    def verify_columns(wrapped, instance, args, kwargs):
        ret_df = wrapped(*args, **kwargs)
        assert isinstance(ret_df, pd.DataFrame)
        req_cols = set(cols)
        now_cols = set(ret_df.columns)
        missing_cols = req_cols-now_cols
        assert missing_cols == set([]), (missing_cols, wrapped.__name__)
        return ret_df
    return verify_columns

