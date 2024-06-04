#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: 2UE
# Author: Harish
# GNU Radio version: 3.8.3.1

# used to compare version numbers of the Qt widget 
from distutils.version import StrictVersion

# if this script is run directly (not imported as a module) then this code will run
if __name__ == '__main__':
    # allows us to access shared language libraries
    import ctypes
    # get system information
    import sys
    if sys.platform.startswith('linux'):
        try:
            # library used as a window system for Unix-like systems
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

# gnuradio helps us implement software radios
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
import sys
# helps us handle signals to and from the virtualized radios
import signal
# helps represent the GUI of the GNURadio
from PyQt5 import Qt
# helps us use command line interfaces
from argparse import ArgumentParser
# helps us parse arguments in GNU Radio
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
# helps GNU Radio interface with ZeroMQ
from gnuradio import zeromq
from gnuradio import qtgui

class top_block(gr.top_block, Qt.QWidget):
    # create the GUI for the GNU Radio flowgraph using the Qt widget
    def __init__(self):
        gr.top_block.__init__(self, "2UE")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("2UE")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "top_block")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 23.04e6

        ##################################################
        # Blocks
        ##################################################
        # source blocks send requests to a certain port
        self.zeromq_req_source_3 = zeromq.req_source(gr.sizeof_gr_complex, 1, 'tcp://localhost:2101', 100, False, -1)
        self.zeromq_req_source_1 = zeromq.req_source(gr.sizeof_gr_complex, 1, 'tcp://localhost:2001', 100, False, -1)
        self.zeromq_req_source_0 = zeromq.req_source(gr.sizeof_gr_complex, 1, 'tcp://localhost:2011', 100, False, -1)
        # sink blocks listens for requests on a certain port, and sends a reply when it receives it
        # sends and receives connections with the eNB and UE built on top of virtualized radios
        self.zeromq_rep_sink_2 = zeromq.rep_sink(gr.sizeof_gr_complex, 1, 'tcp://*:2000', 100, False, -1)
        self.zeromq_rep_sink_1 = zeromq.rep_sink(gr.sizeof_gr_complex, 1, 'tcp://*:2010', 100, False, -1)
        self.zeromq_rep_sink_0 = zeromq.rep_sink(gr.sizeof_gr_complex, 1, 'tcp://*:2100', 100, False, -1)
        # throttle block ensure optimum CPU usage
        self.blocks_throttle_0_0_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)
        self.blocks_throttle_0_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)
        # adds the complex signals it receives
        self.blocks_add_xx_0 = blocks.add_vcc(1)


        ##################################################
        # Connections
        ##################################################
        # connects the blocks together to form the flowgraph
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.zeromq_rep_sink_0, 0))
        self.connect((self.blocks_throttle_0_0, 0), (self.zeromq_rep_sink_2, 0))
        self.connect((self.blocks_throttle_0_0_0, 0), (self.zeromq_rep_sink_1, 0))
        self.connect((self.zeromq_req_source_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.zeromq_req_source_1, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.zeromq_req_source_3, 0), (self.blocks_throttle_0_0, 0))
        self.connect((self.zeromq_req_source_3, 0), (self.blocks_throttle_0_0_0, 0))

    # save and close the Qt widget
    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    # sets appropriate sample rate for the blocks in the CPU
    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle_0_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle_0_0_0.set_sample_rate(self.samp_rate)

# effectively implements the flowgraph defined above
def main(top_block_cls=top_block, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        # if the version used is appropriate, a certain graphic system is selected
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    def quitting():
        tb.stop()
        tb.wait()

    qapp.aboutToQuit.connect(quitting)
    qapp.exec_()

if __name__ == '__main__':
    main()
