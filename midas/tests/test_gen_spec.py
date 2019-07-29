from midas import Midas

m = Midas()
cars_df = m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')
small_df = cars_df.head(5)
m.register_df(small_df, "small_df")
w = m.get_current_widget()
print(w._spec_source)