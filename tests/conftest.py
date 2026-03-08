import pytest


@pytest.fixture(autouse=True, scope='session')
def matplotlib_backend():
    import matplotlib.pyplot as plt
    plt.switch_backend('agg')
