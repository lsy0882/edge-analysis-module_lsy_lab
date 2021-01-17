
from PyQt5 import QtCore, QtWidgets, QtGui

class VideoViewer(QtWidgets.QWidget):
    def __init__(self, parent=None, width=640, height=360):
        super(VideoViewer, self).__init__(parent)
        self.image = QtGui.QImage()
        self.image.scaledToWidth(width)
        self.image.scaledToWidth(height)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        self.setFixedWidth(width)
        self.setFixedHeight(height)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.image = QtGui.QImage()

    @QtCore.pyqtSlot(QtGui.QImage)
    def setImage(self, image):
        if image.isNull():
            print("Viewer Dropped frame!")

        self.image = image
        if image.size() != self.size():
            self.setFixedSize(image.size())
        self.update()

