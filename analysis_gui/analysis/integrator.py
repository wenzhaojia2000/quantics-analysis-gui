# -*- coding: utf-8 -*-
'''
@author: 19081417

Consists of the single class that provides functionality for the 'Analyse
Integrator' tab of the analysis GUI.
'''

from pathlib import Path
import re
from pyqtgraph import BarGraphItem
from ..ui.analysis_tab import AnalysisTab

class AnalysisIntegrator(AnalysisTab):
    '''
    Promoted widget that defines functionality for the "Analyse Integrator" tab
    of the analysis GUI.
    '''
    def __init__(self):
        '''
        Constructor method. Loads the UI file.
        '''
        super().__init__(Path(__file__).parent/'integrator.ui')

    def activate(self):
        '''
        Activation method. See the documentation in AnalysisTab._activate for
        information.
        '''
        methods = {
            0: self.rdsteps,  # analyse step size
            1: self.rdtiming, # look at timing file
            2: self.rdspeed,  # plot speed file
            3: self.rdupdate, # plot update file
        }
        options = {
            1: self.timing_box,
            3: self.update_box
        }
        required_files = {
            0: ['steps'],
            1: ['timing'],
            2: ['speed'],
            3: ['update']
        }
        super().activate(methods, options, required_files)

    def rdsteps(self):
        '''
        Not implemented as the corresponding quantics analysis program is
        currently broken.
        '''
        raise NotImplementedError

    def rdtiming(self):
        '''
        Reads the timing file, which is expected to be in the format

        [host, time, directory information]
        Subroutine  Calls N  cpu/N    cpu      %cpu     Clock
        name.1      a.1      b.1      c.1      d.1      e.1
        name.2      a.2      b.2      c.2      d.2      e.2
        ...         ...      ...      ...      ...      ...
        name.m      a.m      b.m      c.m      d.m      e.m

        Total ...
        [any other information]

        name should be a string, and other cells should be in a numeric form
        that can be converted into a float like 0.123 or 1.234E-10, etc.

        Plots a bar graph of the column selected by the user, and also outputs
        the timing file sorted by the selected column in the text tab.
        '''
        filepath = self.window().dir.cwd/'timing'
        with open(filepath, mode='r', encoding='utf-8') as f:
            txt = f.read()
        # split after 'Clock' and before 'Total' (see docstring), so we have
        # three strings, with the middle being the data
        splits = re.split(r'(?<=Clock)\n|\n(?=Total)', txt, flags=re.IGNORECASE)
        if len(splits) != 3:
            raise ValueError('Invalid timing file')
        pre, txt, post = splits

        arr = []
        for line in txt.split('\n'):
            # should find one name and five floats per line (name, a, b, c, d,
            # e). after splitting by whitespace, floats should take up the last
            # 5 entries, and the name take up the rest
            row = re.findall(r'\S+', line)
            if len(row) >= 5:
                name = ' '.join(row[:-5])
                floats = row[-5:]
                # floats are still strings, need to convert. the last entry is
                # the line itself, which is already formatted in a nice way.
                # this saves manually formatting the data
                arr.append(tuple([name] + list(map(float, floats)) + [line]))
        if len(arr) == 0:
            # nothing found?
            raise ValueError('Invalid timing file')

        # sort by column chosen by user
        if self.timing_sort.currentIndex() == 0:
            # sort by name
            arr.sort(key=lambda x: x[0])
        else:
            # sort by number (largest first)
            arr.sort(key=lambda x: -x[self.timing_sort.currentIndex()])
        self.window().data = arr

        # display sorted text
        txt = "\n".join([line[-1] for line in self.window().data])
        self.window().text.setPlainText(f'{pre}\n{txt}\n\n{post}')
        self.window().plot.reset()

        # start plotting
        self.window().plot.setLabels(title='Subroutine timings', left='')
        # this is a horizontal bar chart so everything is spun 90 deg. can't
        # do a normal vertical one as pyqtgraph can't rotate tick names (yet)
        if self.timing_sort.currentIndex() == 0:
            # plot cpu if 'name' is selected (names don't have values)
            values = [row[3] for row in self.window().data]
            self.window().plot.setLabels(bottom='CPU')
        else:
            values = [row[self.timing_sort.currentIndex()] for row in self.window().data]
            self.window().plot.setLabels(bottom=self.timing_sort.currentText())
        names = [row[0] for row in self.window().data]
        positions = list(range(1, len(values)+1))
        bar = BarGraphItem(x0=0, y=positions, height=0.6, width=values)
        self.window().plot.addItem(bar)
        # sort out bar chart ticks https://stackoverflow.com/questions/72002352
        ticks = []
        for i, label in enumerate(names):
            ticks.append((positions[i], label))
        self.window().plot.getAxis('left').setTicks([ticks])

    def rdspeed(self):
        '''
        Reads the speed file, which is expected to be in the format

        # [Lines beginning with # are ignored.]
        t.1     cpu.1     d.1     date.1    real[s].1    real[h].1
        t.2     cpu.2     d.2     date.2    real[s].2    real[h].2
        ...     ...       ...     ...       ...          ...
        t.m     cpu.m     d.m     date.m    real[s].m    real[h].m

        where t is the propagation time, cpu is the CPU time, d is the delta in
        CPU time (ignored), date is the date in form MMM DD hh:mm:ss (ignored),
        and real is the real time in seconds [s] or hours [h] (hours ignored).

        Plots the CPU time and real time against propagation time (d can be
        re-calculated using a dy/dx transform in the context menu in pyqtgraph).
        '''
        filepath = self.window().dir.cwd/'speed'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            txt = f.read()
            self.window().text.setPlainText(txt)
            # for readFloats to work the date column in the file needs to be
            # removed. match any dates and replace them with nothing
            date_regex = r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'
            lines = re.sub(date_regex, '', txt).split('\n')
            try:
                self.window().data = self.readFloats(lines, 5, ignore_regex=r'^#')
            except ValueError:
                raise ValueError('Invalid speed file') from None

        # start plotting
        self.window().plot.reset(switch_to_plot=True)
        self.window().plot.setLabels(title='Speed file',
                                     bottom='Propagation time (fs)', left='Time (s)')
        self.window().plot.plot(self.window().data[:, 0], self.window().data[:, 1],
                                name='CPU time', pen='r')
        self.window().plot.plot(self.window().data[:, 0], self.window().data[:, 3],
                                name='Real time', pen='b')

    def rdupdate(self):
        '''
        Reads the update file, which is expected to be in the format, where
        each cell is a float,

        n.1    y1.1    y2.1    y3.1    t.1
        n.2    y1.2    y2.2    y3.2    t.2
        ...    ...     ...     ...     ...
        n.m    y1.m    y2.m    y3.m    t.m

        where n is the update step number (ignored), y1 is step size, y2 is
        error of the coefficients (A), y3 is error of the SPFs (phi), and t
        is time.

        Plots the step or the errors against time, depending on the task chosen.
        Incomplete lines (failed steps) are not included. Note that this
        function does not use the 'rdupdate' command.
        '''
        filepath = self.window().dir.cwd/'update'
        # assemble data matrix
        with open(filepath, mode='r', encoding='utf-8') as f:
            self.window().text.setPlainText(f.read())
            f.seek(0)
            try:
                self.window().data = self.readFloats(f, 5, ignore_regex=r'^#')
            except ValueError:
                raise ValueError('Invalid update file') from None

        # start plotting, depending on options
        self.window().plot.reset(switch_to_plot=True)
        if self.update_task.currentIndex() == 0:
            self.window().plot.setLabels(title='Update file errors',
                                         bottom='Time (fs)', left='Error')
            self.window().plot.plot(self.window().data[:, 4], self.window().data[:, 2],
                                    name='Error of A-vector', pen='r')
            self.window().plot.plot(self.window().data[:, 4], self.window().data[:, 3],
                                    name='Error of SPFs', pen='b')
        else:
            self.window().plot.setLabels(title='Update file step size',
                                         bottom='Time (fs)', left='Step size (fs)')
            self.window().plot.plot(self.window().data[:, 4], self.window().data[:, 1],
                                    name='Step size', pen='r')
