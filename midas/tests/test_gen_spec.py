from midas import Midas
from midas.showme import gen_spec

m = Midas()
cars_df = m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')

def test_basic():
    small_df = cars_df.head(5)
    m.register_df(small_df, "small_df")
    w = m.get_current_widget()
    print(w._spec_source)

def test_agg_categorical():
    origin_df = m.loc('cars_df', 'origin_df', columns=['Origin'])
    spec = gen_spec(origin_df)
    print(spec)

test_agg_categorical()