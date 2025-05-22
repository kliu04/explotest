from math import sin, pi
import pandas as pd
import numpy as np
import dill

values = pd.read_csv(r"./A17.csv", names=[r"f"])

n = values.iloc[-1].name

dx = pi/n

x_axis = np.arange(0, np.pi + dx, dx)

values['x'] = x_axis

def tr_rule(f: pd.Series, x: pd.Series, dx: float, R: int):
    with open('f.pkl', 'wb') as f_file, open('x.pkl', 'wb') as x_file, open('dx.pkl', 'wb') as dx_file, open('R.pkl', 'wb') as R_file:
        dill.dump(f, f_file)
        dill.dump(x, x_file)
        dill.dump(dx, dx_file)
        dill.dump(R, R_file)
    return (
        (2 / pi) * dx * (
            (1/2 * f.iloc[0] * sin(R * x.iloc[0])) +
            sum(f.iloc[1:-1] * (x.iloc[1:-1] * R).map(sin)) +
            (1/2 * f.iloc[-1] * sin(R * x.iloc[-1]))
        )
    )

tr_rule(values['f'], values['x'], dx, 1)
