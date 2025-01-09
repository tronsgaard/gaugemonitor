import sys
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

def plot_files(filenames):
    
    matplotlib.use('qt5agg')
    fig, ax = plt.subplots()
    
    for f in filenames:
        data = pd.read_csv(f, delim_whitespace=True, names=('date', 'time', 'pressure'))
        data['datetime'] = pd.to_datetime(data.date + ' ' + data.time)
        ax.plot(data.datetime, data.pressure, '.-')
    
    # Decorate axes
    ax.set_xlabel('Time')
    ax.set_ylabel('Pressure (mbar)')
    ax.set_yscale('log')
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('No filename supplied..')
        sys.exit()
    filenames = sys.argv[1:]
    plot_files(filenames) 