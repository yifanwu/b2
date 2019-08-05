from midas import Midas
from midas.showme import gen_spec
import json

m = Midas()
cars_df = m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')

def _shared_gen_spec(df):
    spec = gen_spec(df)
    ps = json.dumps(spec, indent=4)
    print(ps)


def test_basic_flow():
    small_df = cars_df.head(5)
    m.register_df(small_df, "small_df")
    w = m.get_current_widget()
    print(w._spec_source)


def test_agg_categorical():
    origin_df = m.loc('cars_df', 'origin_df', columns=['Origin'])
    _shared_gen_spec(origin_df)


def test_scatter():
    small_df = cars_df.head(5)
    _shared_gen_spec(small_df)


def test_agg_linear():
    displacement_df = m.loc('cars_df', 'origin_df', columns=['Displacement'])
    _shared_gen_spec(displacement_df)


# test_agg_categorical()
# test_agg_linear()
test_scatter()