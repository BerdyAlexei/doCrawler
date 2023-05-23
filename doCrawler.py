from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont,QFontDatabase, QPalette, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QComboBox, QCheckBox, QFileDialog, QLabel, QLineEdit, QPushButton, QPlainTextEdit, QVBoxLayout, QScrollArea, QWidget, QProgressBar, QHBoxLayout, QTextEdit
import docx, os, json, PyPDF2, subprocess
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

# Made by Alejandro Morales Jaime (also known as Berdy Alexei). (づ￣ 3￣)づ

class RWidgets():
    def __init__(self):
        pass

    @staticmethod
    def configBasic(widget, x, y, width, height, text, style, cursor):
        widget.move(x, y)
        widget.setFixedSize(width, height)
        if cursor:
            widget.setCursor(cursor)
        widget.setPlaceholderText(text) if (isinstance(widget, QComboBox) or isinstance(widget, QPlainTextEdit)) else widget.setText(text)

        try:
            widget.setStyleSheet(Path(style).read_text())
        except:
            pass

    class RPushButton(QPushButton):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class RCheckBox(QCheckBox):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class RTextEdit(QTextEdit):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class RLineEdit(QLineEdit):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class SLineEdit(QLineEdit):
        clicked = pyqtSignal()
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton: self.clicked.emit()
            else: super().mousePressEvent(event)

    class RComboBox(QComboBox):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class RPlainTextEdit(QPlainTextEdit):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

    class RLabel(QLabel):
        def __init__(self, x, y, width, height, text, style, cursor, *args, **kwargs):
            super().__init__(*args, **kwargs)
            RWidgets.configBasic(self, x, y, width, height, text, style, cursor)

class doCrawler(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('doCrawler')
        self.setFixedSize(430, 496)
        self.setWindowIcon(QIcon('./data/resources/doCrawler.ico'))

        #Cargar
            #Datos
        with open('./data/data.json','r', encoding='utf-8') as f:
            self.data=json.load(f)
            #Lenguaje
        with open(f'./data/lang/{self.data["lang"]}.json','r') as f:
            self.lang=json.load(f)

        #Variables
        self.threadStart = None
        self.stopFlag = False
        self.itemsList = []

        self.iconFont = QFont()
        self.iconFont.setFamily('BreeziFont')
        self.iconFont.setPointSize(16)
        fontDB = QFontDatabase()
        fontID = fontDB.addApplicationFont('data/resources/fonts/breezi_font-webfont.ttf')
        if fontID != -1:
            fontSTR = fontDB.applicationFontFamilies(fontID)[0]
            self.iconFont.setFamily(fontSTR)

        #Widgets
            #self.selectedFolder.text() donde buscar
        self.selectedFolder = RWidgets.SLineEdit(58, 12, 360, 32, None, None, Qt.PointingHandCursor)
        self.selectedFolder.setReadOnly(True)
        self.selectedFolder.setPlaceholderText(self.lang['selectedFolder'])
        self.selectedFolder.setAlignment(QtCore.Qt.AlignCenter)
        self.openFolder = RWidgets.RPushButton(12, 12, 40, 32, 'f', None, Qt.PointingHandCursor)
        self.openFolder.setFont(self.iconFont)
            #Texto a buscar
        self.textToSearch = RWidgets.RLineEdit(12, 50, 406, 32+8, None, None, None)
        self.textToSearch.setPlaceholderText(self.lang['textToSearch'])
        self.textToSearch.setAlignment(QtCore.Qt.AlignCenter)
        self.textToSearch.setMaxLength(252)
        self.textCharacters = RWidgets.RLabel(350, 98, 64, 32, '0/252', None, None, None)
        self.textCharacters.setAlignment(QtCore.Qt.AlignRight)
        self.textCharacters.setDisabled(True)
        self.clearTextToSearch = RWidgets.RPushButton(218, 88+32, 200, 32, self.lang['clearTextToSearch'], None, Qt.PointingHandCursor)
        self.searchTextToSearch = RWidgets.RPushButton(12, 88+32, 200, 32, self.lang['searchTextToSearch'], None, Qt.PointingHandCursor)
        self.searchTextToSearch.setDisabled(True)
            #Lectura
        self.readingProcess = QProgressBar()
        self.readingProcess.setFormat(None)
        self.readingProcess.setFixedSize(406, 32)
        self.readingProcess.move(12, 386+32)
        self.readingConsole = RWidgets.RLabel(12, 386+32, 406, 32, None, None, None)
        self.readingConsole.setAlignment(QtCore.Qt.AlignCenter)
        self.readingStop = RWidgets.RPushButton(12, 348+32, 406, 32, self.lang['readingStop'], None, Qt.PointingHandCursor)
        self.readingStop.setDisabled(True)
            #Layout
        self.filesFoundLayout = QVBoxLayout()
        self.filesFoundScroll = QScrollArea()
        self.filesFoundScroll.setWidgetResizable(True)
        self.filesFoundWidget = QWidget(self.filesFoundScroll)
        self.scrollLayout = QVBoxLayout(self.filesFoundWidget)
        self.filesFoundScroll.setWidget(self.filesFoundWidget)
        self.filesFoundScroll.setFixedSize(406, 218)
        self.filesFoundScroll.move(12, 126+32)
        self.filesFoundLayout.addWidget(self.filesFoundScroll)
        self.scrollLayout.addItem(QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        self.copyRight = RWidgets.RLabel(0, 480-24, 430, 32, 'Copyright © Jass Design Group 2023. All Rights Reserved', None, None, None)
        self.copyRight.setAlignment(QtCore.Qt.AlignCenter)
        self.copyRight.setDisabled(True)

        
        for i in [
        self.openFolder,
        self.selectedFolder,
        self.textToSearch,
        self.textCharacters,
        self.clearTextToSearch,
        self.searchTextToSearch,
        self.filesFoundScroll,
        self.readingProcess,
        self.readingConsole,
        self.readingStop,
        self.copyRight
        ]:
            self.layout().addWidget(i)

        #Cargar - Funciones
        def _loadFolder(folder):
            self.selectedFolder.setText(folder)

        def _setEnabledByText(widget, condition, secondary = None, secondaryCondition = None):
            if condition.text() and (not secondary or secondaryCondition.text()):
                widget.setEnabled(True)
            else:
                widget.setDisabled(True)

        
        #Cargar - Condiciones
        if self.data['vars']['folder']:

            _loadFolder(self.data['vars']['folder'])

        else:

            _loadFolder(os.path.expanduser('~/Documents'))

        
        #Guardar
        def _saveData():
            self.data['vars']['folder'] = (self.selectedFolder.text() if os.path.isdir(self.selectedFolder.text()) else '')

            with open('./data/data.json', 'w') as f:
                json.dump(self.data, f, indent = 4)
        
        #Funciones
        def openFolder():
            folderPath = QFileDialog.getExistingDirectory(self, self.lang['selectFolder'])

            if folderPath:
                self.selectedFolder.setText(folderPath)

            _loadFolder(self.data['vars']['folder'])

        
        def clearText(widget):
            widget.clear()

        def stateEnable(bool):
            for i in [
                self.openFolder,
                self.selectedFolder,
                self.textToSearch,
                self.clearTextToSearch,
                self.searchTextToSearch
            ]:
                i.setEnabled(bool)
            if bool:
                self.readingStop.setEnabled(False)
            else:
                self.readingStop.setEnabled(True)

        #Funciones - Threads
        def _threadStart():
            stateEnable(False)

            self.thread = searchThread(self.selectedFolder.text(), self.textToSearch.text(), 30)

            self.thread.loadingMaxSignal.connect(lambda loadingMax: self.readingProcess.setMaximum(loadingMax))
            self.thread.loadingStateSignal.connect(lambda loadingState: self.readingProcess.setValue(loadingState))
            self.thread.filesFoundSignal.connect(lambda fileAmount: self.readingConsole.setText(self.lang['filesFound'].format(fileAmount)))
            self.thread.notFoundSignal.connect(lambda: self.readingConsole.setText(self.lang['filesNotFound']))
            self.thread.readingSignal.connect(lambda fileName: self.readingConsole.setText(self.lang['readingConsole'].format(fileName)))
            self.thread.enableSignal.connect(lambda: stateEnable(True))

            self.thread.generateListSignal.connect(lambda dict: _generateList(dict))

            self.thread.start()


        def _threadStop():
            self.readingStop.setDisabled(True)
            self.readingConsole.setText(self.lang['readingStopProcess'])
            self.thread.stop()

        def _generateList(dict):
            key = list(dict.keys())[0]
            value = list(dict.values())[0]

            fileType = True if key.split('.')[1] == 'pdf' else False

            fileName = QLabel()
            fileName.setFixedSize(291, 32)

            openFolder = QPushButton('f')
            openFolder.setFont(self.iconFont)
            openFolder.setFixedSize(32, 32)
            openFolder.setCursor(Qt.PointingHandCursor)
            openFile = QPushButton('d')
            openFile.setFont(self.iconFont)
            openFile.setFixedSize(32, 32)
            openFile.setCursor(Qt.PointingHandCursor)

            if fileType:
                page = value.split('#')[len(value.split('#')) - 1]
                fileName.setText('({} #{}) {}'.format(self.lang['page'], page, key))

                value = value.replace(('#' + page), '')
            else:
                fileName.setText(key)

            openFile.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(value)))
            openFolder.clicked.connect(lambda: subprocess.Popen(['explorer', '/select,', '/n,', os.path.abspath(value)]))
            
            hLayout = QHBoxLayout()
            hLayout.setSpacing(6)

            for i in [
                fileName,
                openFolder,
                openFile
            ]:
                hLayout.addWidget(i)
            
            self.scrollLayout.addLayout(hLayout)
            self.itemsList.append((hLayout, fileName, openFolder, openFile))

        def _clearLayout():
            for item in self.itemsList:
                hLayout, fileName, openFolder, openFile = item
                fileName.deleteLater()
                openFolder.deleteLater()
                openFile.deleteLater()
                hLayout.deleteLater()
            self.itemsList = []


        #Eventos
            #Añadir a carácteres permitidos
        self.openFolder.clicked.connect(lambda:openFolder())
        self.selectedFolder.clicked.connect(lambda:openFolder())
        self.selectedFolder.textChanged.connect(lambda:_saveData())
        self.selectedFolder.textChanged.connect(lambda:_setEnabledByText(self.searchTextToSearch, self.textToSearch, True, self.selectedFolder))
        self.textToSearch.textChanged.connect(lambda:self.textCharacters.setText(f'{len(self.textToSearch.text())}/252'))
        self.textToSearch.textChanged.connect(lambda:_setEnabledByText(self.searchTextToSearch, self.textToSearch, True, self.selectedFolder))
        self.textToSearch.textChanged.connect(lambda:_setEnabledByText(self.clearTextToSearch, self.textToSearch))
        self.clearTextToSearch.clicked.connect(lambda:clearText(self.textToSearch))
        self.clearTextToSearch.clicked.connect(lambda:_clearLayout())
        self.searchTextToSearch.clicked.connect(lambda:stateEnable(False))
        self.searchTextToSearch.clicked.connect(lambda:_threadStart())
        self.searchTextToSearch.clicked.connect(lambda:_clearLayout())
        self.readingStop.clicked.connect(lambda:_threadStop())

        #Inicializar funciones
        for widget, condition in {
        self.searchTextToSearch: self.textToSearch, 
        self.clearTextToSearch: self.textToSearch
        }.items():
            _setEnabledByText(widget, condition)

class searchThread(QThread):
    generateListSignal = pyqtSignal(dict)
    loadingMaxSignal = pyqtSignal(int)
    loadingStateSignal = pyqtSignal(int)
    filesFoundSignal = pyqtSignal(int)
    notFoundSignal = pyqtSignal()
    readingSignal = pyqtSignal(str)
    enableSignal = pyqtSignal(bool)

    def __init__(self, selectedFolder, textToSearch, seconds):
        super().__init__()
        self.selectedFolder = selectedFolder
        self.textToSearch = textToSearch
        self.seconds = seconds
        self.stopFlag = False
        self.executor = ThreadPoolExecutor(max_workers = 1)

    def stop(self):
        self.stopFlag = True

    def fileRead(self, filePath, fileName):
        if fileName.endswith('.docx'):
            for i, para in enumerate(docx.Document(filePath).paragraphs):
                if self.textToSearch in para.text:
                    return filePath
        elif fileName.endswith('.txt'):
            with open(filePath, 'r', encoding='iso-8859-1') as file:
                for i, line in enumerate(file.readlines()):
                    if self.textToSearch in line:
                        return filePath
        elif fileName.endswith('.pdf'):
            with open(filePath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i in range(len(reader.pages)):
                    if self.textToSearch in reader.pages[i].extract_text():
                        return f'{filePath}#{i + 1}'

    def readTimeout(self, filePath, fileName, timeout):
        future = self.executor.submit(self.fileRead, filePath, fileName)
        try:
            result = wait([future], timeout=timeout)[0].pop().result()
        except:
            result = None
        return result

    def run(self):
        filesFound = {}
        for path, names, fileNames in os.walk(self.selectedFolder):
            self.loadingMaxSignal.emit(len(fileNames))
            loading = 0
            self.loadingStateSignal.emit(loading)
            if self.stopFlag:
                break
            for fileName in fileNames:
                if self.stopFlag:
                    break
                loading += 1
                self.loadingStateSignal.emit(loading)
                try:
                    if any(fileName.endswith(ext) for ext in ['.docx', '.txt', '.pdf']):
                        self.readingSignal.emit(fileName)
                        filePath = os.path.join(path, fileName)
                        result = self.readTimeout(filePath, fileName, self.seconds)
                        if result is not None:
                            self.generateListSignal.emit({fileName:result})
                            filesFound.setdefault(fileName, result)

                except:
                    continue

        if filesFound:
            self.filesFoundSignal.emit(len(filesFound))
        else:
            self.notFoundSignal.emit()

        self.loadingMaxSignal.emit(0)
        self.loadingStateSignal.emit(0)
        self.enableSignal.emit(True)


if __name__ == '__main__':
    aplication = QtWidgets.QApplication([])
    aplication.setPalette(QPalette())
    aplication.setStyleSheet(Path('data/resources/css/main.css').read_text())

    
    mainWindow = doCrawler()
    mainWindow.show()

    aplication.exec_()