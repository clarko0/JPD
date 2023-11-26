import sys
import typing
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget


class Overlay(QtWidgets.QWidget):

    def __init__(self, parent=None, windowSize=24, penWidth=2, weapon="AK", scope="Nil") -> None:
        QtWidgets.QWidget.__init__(self, parent)
        self.weapon = weapon
        self.scope = scope
        self.windowSize = windowSize
        self.resize(500, 600)
        self.pen = QtGui.QPen(QtGui.QColor(231, 60, 126, 255))
        self.pen.setWidth(penWidth)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.move(QtWidgets.QApplication.desktop().screen().rect(
        ).center() - self.rect().center() + QtCore.QPoint(1, 1))
        self.setWindowFlag(QtCore.Qt.Tool)
        self.setWindowTitle("clarko tool")

    def paintEvent(self, event):
        ws = self.windowSize
        d = 5
        painter = QtGui.QPainter(self)
        painter.setPen(self.pen)
        painter.drawText(250, 250, self.weapon.split("_")[1])
        # painter.drawText(3, 60, self.scope)
