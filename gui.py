#!/usr/bin/env python3

import lib27gn950

import hid
# https://pypi.org/project/hid/
# https://github.com/apmorton/pyhidapi

import re
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class Gui(QWidget):
	def __init__(self):
		super().__init__()
		self.init_ui()


	def init_ui(self):
		self.setWindowTitle('27g950controller')

		mainLayout = QVBoxLayout(self)

		self.selectionbuttonslayout = QHBoxLayout(self)
		self.selectionbuttonslayout.addWidget(QLabel('<b>Select monitors: </b>'))
		mainLayout.addLayout(self.selectionbuttonslayout)

		mainLayout.addWidget(QLabel(''))

		powerbuttonslayout = QGridLayout(self)
		powerbuttonslayout.addWidget(QLabel('<b>Power</b>'), 0, 0, 1, 2)
		x = QPushButton('Turn on')
		x.clicked.connect(self.turn_on)
		powerbuttonslayout.addWidget(x, 1, 0)
		x = QPushButton('Turn off')
		x.clicked.connect(self.turn_off)
		powerbuttonslayout.addWidget(x, 1, 1)
		mainLayout.addLayout(powerbuttonslayout)

		mainLayout.addWidget(QLabel(''))

		brightnessbuttonslayout = QGridLayout(self)
		brightnessbuttonslayout.addWidget(QLabel('<b>Brightness</b>'), 0, 0, 1, 6)
		for i in range(1, 13):
			x = QPushButton(str(i))
			x.clicked.connect(lambda _, i=i: self.set_brightness(i))
			row = 1 + i//7
			col = i - 1 - (6 if i > 6 else 0)
			brightnessbuttonslayout.addWidget(x, row, col)
		mainLayout.addLayout(brightnessbuttonslayout)

		mainLayout.addWidget(QLabel(''))

		configbuttonslayout = QGridLayout(self)
		configbuttonslayout.addWidget(QLabel('<b>Lighting mode</b>'), 0, 0, 1, 4)
		for i in range(4):
			x = QPushButton(f'Color {i+1}')
			x.clicked.connect(lambda _, i=i: self.set_static_color(i+1))
			configbuttonslayout.addWidget(x, 1, i)
		x = QPushButton('Peaceful')
		x.clicked.connect(self.set_peaceful_color)
		configbuttonslayout.addWidget(x, 2, 0, 1, 2)
		x = QPushButton('Dynamic')
		x.clicked.connect(self.set_dynamic_color)
		configbuttonslayout.addWidget(x, 2, 2, 1, 2)
		mainLayout.addLayout(configbuttonslayout)

		mainLayout.addWidget(QLabel(''))

		editbuttonslayout = QGridLayout(self)
		editbuttonslayout.addWidget(QLabel('<b>Edit static colors</b>'), 0, 0, 1, 4)
		x = QLabel('Enter new color: ')
		editbuttonslayout.addWidget(x, 1, 0, 1, 2)
		self.colorInputBox = QLineEdit()
		self.colorInputBox.textChanged.connect(self.validate_new_color)
		editbuttonslayout.addWidget(self.colorInputBox, 1, 2, 1, 2)
		self.colorValidationOutputBox = QLabel('Your entry is: invalid')
		editbuttonslayout.addWidget(self.colorValidationOutputBox, 2, 0, 1, 4)
		for i in range(4):
			x = QPushButton(f'Set {i+1}')
			x.clicked.connect(lambda _, i=i: self.set_color(i+1))
			editbuttonslayout.addWidget(x, 3, i)
		import textwrap
		x = QLabel(textwrap.dedent('''
			Enter a lowercase RGB hex string, where each R/G/B is one of:
			  00   20   40   80   a0   c0   e0   ff
			Corresponding to decimal values:
			  00   32   64  128  160  192  224  255

			One R/G/B channel must be ff and one must be 00.
			The other channel can be anything.
			The only exception is that white (ffffff) is allowed.\
		'''))
		editbuttonslayout.addWidget(x, 4, 0, 1, 4)
		mainLayout.addLayout(editbuttonslayout)


	def init_monitors(self):
		monitors = lib27gn950.find_monitors()
		if not monitors:
			for item in self.layout().children():
				self.layout().removeItem(item)
			self.layout().addWidget(QLabel('No monitors found'))
			return

		self.devs = []
		for monitor in monitors:
			self.devs.append(hid.Device(path=monitor['path']))

		self.selection = list(range(len(self.devs)))

		for i in self.selection:
			x = QCheckBox(str(i+1))
			x.setCheckState(2)
			x.stateChanged.connect(lambda checked, i=i: self.update_selection(i, checked))
			self.selectionbuttonslayout.addWidget(x)


	def cleanup(self):
		if hasattr(self, 'devs'):
			for dev in self.devs:
				dev.close()


	def validate_new_color(self, text):
		if text in lib27gn950.valid_colors:
			self.colorValidationOutputBox.setText('Your entry is: valid')
		else:
			self.colorValidationOutputBox.setText('Your entry is: invalid')


	def update_selection(self, monitor_num, checked):
		if checked == 0:
			self.selection.remove(monitor_num)
		elif checked == 2:
			self.selection.append(monitor_num)


	def send_command(self, cmd):
		devs = []
		for i in self.selection:
			devs.append(self.devs[i])
		lib27gn950.send_command(cmd, devs)


	def turn_on(self):
		cmd = lib27gn950.control_commands['turn_on']
		self.send_command(cmd)
	def turn_off(self):
		cmd = lib27gn950.control_commands['turn_off']
		self.send_command(cmd)

	def set_static_color(self, color):
		cmd = lib27gn950.control_commands['color' + str(color)]
		self.send_command(cmd)
	def set_peaceful_color(self):
		cmd = lib27gn950.control_commands['color_peaceful']
		self.send_command(cmd)
	def set_dynamic_color(self):
		cmd = lib27gn950.control_commands['color_dynamic']
		self.send_command(cmd)

	def set_brightness(self, brt):
		cmd = lib27gn950.brightness_commands[brt]
		self.send_command(cmd)

	def set_color(self, slot):
		color = self.colorInputBox.text()
		if color not in lib27gn950.valid_colors:
			return
		cmd = lib27gn950.get_set_color_command(slot, color)
		self.send_command(cmd)


app = QApplication(sys.argv)
try:
	x = Gui()
	x.init_monitors()
	x.show()
	sys.exit(app.exec_())
finally:
	if 'x' in locals():
		x.cleanup()
