from datetime import datetime
from time import sleep, time_ns
from random import random
import numpy as np
import matplotlib, matplotlib.pyplot as plt, matplotlib.transforms as transforms
from matplotlib.dates import ConciseDateFormatter, DateFormatter
#import sqlite3
import sys
from os.path import dirname, join
from os import makedirs
import logging
#from edwardsserial.tic import TIC

TIC_PORT = 'COM2'

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    return logger

class TIC:
    def __init__(self, port, gauges, memory=200, emulate=False):
        """Setup TIC connection"""
        self.emulate = emulate
        if emulate is False:
            from edwardsserial.tic import TIC
            self.tic = TIC('COM2')
        
        # Initialize SQLite3 database for storing data
        #self.db = sqlite3.connect('tmp.db')
        #cursor = self.db.cursor()
        #cursor.execute('CREATE TABLE data(timestamp_ns BIGING, gauge_no INT, pressure FLOAT)')
        
        # Make a dict of arrays, one for each gauge, for storing the most recent data
        self.data = dict()
        for gauge_no in gauges:
            self.data[gauge_no] = np.full((memory, 2), np.nan)
        
        # Open files for logging
        self.files = dict()
        datestr = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        logdir = join(dirname(__file__), 'logs')
        makedirs(logdir, exist_ok=True)
        for gauge_no in gauges:
            fname = join(logdir, f'{datestr}_gauge{gauge_no}.txt')
            logger.info(f'Opening file for logging: {fname}')
            self.files[gauge_no] = open(fname, 'w', buffering=1)

    def store_data(self, gauge_no, t, pressure):
        """Store data in cache and write to file"""
        cache = self.data[gauge_no]
        cache = np.roll(cache, 1, axis=0)  # Shift the cache by one
        cache[0] = (t, pressure)  # Overwrite oldest entry
        self.data[gauge_no] = cache
        # TODO: Write line to ascii file (one file for each gauge?)

    def read_gauge(self, gauge_no):
        """Return <DateTime> object and pressure in mbar"""
        # Get time
        t = 1e-9 * time_ns()
        
        # Emulate or read from TIC
        if self.emulate:
            pressure = 1050*random()
            old = self.data[gauge_no][0,1]
            if np.isfinite(old):
                pressure = (pressure + 20*old)/21
        else:
            #pressure = self.tic.gauge1.pressure * 1e-2  # mbar
            pressure = getattr(self.tic, f'gauge{gauge_no}').pressure
            if pressure is None:
                pressure = np.nan
            else:
                pressure *= 1e-2
        
        self.store_data(gauge_no, t, pressure)
        
        # Print reading
        datestr = datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S.%f')
        print(f'{gauge_no} - {datestr} - {pressure}')

        # Write to file
        self.files[gauge_no].write(f'{datestr}    {pressure:.5e}\n')

        return t, pressure


class GaugeFigure():
    """Class representing the figure window"""
    
    def __init__(self, nrows=6):
        matplotlib.use('TkAgg')
        plt.ion()  # Interactive on
        self.fig, self.axes = plt.subplots(nrows=nrows, ncols=2, sharex=True, squeeze=False, width_ratios=[2,1])
        self.fig.set_size_inches(16,12)
        self.fig.tight_layout()
        # Setup the left column
        self.axes[-1,0].set_xlabel('Time (seconds)')
        self.axes[nrows//2,0].set_ylabel('Pressure (mbar)')
        self.series = []
        self.gradients = []
        for ax in self.axes[:,0]:
            s = ax.plot([], [], color='brown', marker='o')
            self.series.append(s[0])
            g = ax.plot([], [], color='green', marker='none', linestyle='--', linewidth=2)
            self.gradients.append(g[0])
            ax.set_ylim([0,1050])
        # Setup the right column with text boxes
        self.text = []
        for ax in self.axes[:,1]:
            ax.set_axis_off()
            textbox = ax.text(0, 0.5, f'[]', ha='left', va='center', fontsize=36, color='blue', transform=ax.transAxes)
            self.text.append(textbox)
        # Define time offset, plotting relative to this
        self.t0 = 1e-9 * time_ns()
    
    def update_data(self, row, t, pressure, tsize=200):
        """Dynamically add data points to existing plot"""
        # Update plot in left column
        tt = t-self.t0
        #self.axes[row,0].scatter(tt.seconds, pressure, color='k', marker='.')
        xdata, ydata = self.series[row].get_data()
        xdata = np.hstack((xdata, (tt,)))
        ydata = np.hstack((ydata, (pressure,)))
        self.series[row].set_data((xdata, ydata))
        #self.axes[row,0].plot(xdata, ydata)
        self.axes[0,0].set_xlim(tt-tsize, tt)
        # Recompute data limits and update view limits
        #self.axes[row,0].relim()
        #self.axes[row,0].autoscale_view()
        # Estimate gradient
        coef = np.polyfit(xdata[-10:], ydata[-10:], 1)
        gradient = coef[0]
        tmpx = np.array([xdata[-1]-tsize/4, xdata[-1]])
        self.gradients[row].set_data(tmpx, np.poly1d(coef)(tmpx))
        # Write numbers in right column
        self.text[row].set_text(f'{pressure:.1f} mbar\n({gradient:.1f} mbar/s)')

    def flush(self):
        """Redraw figure with updated data"""
        #logger.info('Start draw')
        self.fig.canvas.draw()
        #logger.info('Start flush')
        self.fig.canvas.flush_events()
        #logger.info('Flush done!')


def run():
    """Main program"""
    logger.info('Starting..')
    #gauges = [1,2,3,4,5,6]
    gauges = [1,2]

    # Setup figure
    fig = GaugeFigure(len(gauges))

    # Initialize connection to TIC
    tic = TIC(TIC_PORT, gauges)

    while True:
        for g in gauges:
            t, pressure = tic.read_gauge(g)
            fig.update_data(g-1, t, pressure)
        fig.flush()
        sleep(0.5)


if __name__ == '__main__':
    logger = setup_logger()
    run()
