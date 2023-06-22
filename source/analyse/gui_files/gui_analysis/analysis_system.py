# -*- coding: utf-8 -*-
'''
@author: 19081417
'''

from PyQt5 import QtWidgets, QtCore
from .ui_base import AnalysisMainInterface, AnalysisTabInterface

class AnalysisSystem(QtWidgets.QWidget, AnalysisTabInterface):
    '''
    Defines functionality for the "Analyse System Evolution" tab of the
    analysis GUI.
    '''
    def __init__(self, owner:AnalysisMainInterface) -> None:
        '''
        Initiation method.
        '''
        super().__init__(owner=owner, push_name='analsys_push',
                         box_name='analsys_layout')

    @QtCore.pyqtSlot()
    def continuePushed(self) -> None:
        '''
        Action to perform when the tab's 'Continue' button is pushed.
        '''
        # working directory
        abspath = self.owner.dir_edit.text()
        # get objectName() of checked radio button (there should only be 1)
        radio_name = [radio.objectName() for radio in self.radio
                      if radio.isChecked()][0]
        match radio_name:
            case 'analsys_1': # plot 1d density evolution
                self.owner.runCmd('showd1d', '-inter', '-i', abspath, input_='1')
            case 'analsys_2': # plot 2d density evolution
                self.owner.runCmd('showsys', '-i', abspath)
            case 'analsys_3': # plot diabatic state population
                self.owner.runCmd('plstate', '-i', abspath)
            case 'analsys_4': # plot potential energy surface
                self.owner.runCmd('showsys', '-pes', '-i', abspath, input_='1')
