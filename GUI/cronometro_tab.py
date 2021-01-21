import datetime

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QSizePolicy, QTextEdit, QLabel, QFormLayout

from GUI.GUI_Resources import get_cronometro_widget_ui, get_cronometro_bar_widget
from GUI.cronometro import Timer
from GUI.pacient_oriented_tab_interface import PacientInterface
from database.Settings import UserSettings
from database.prueba import Prueba


class Cronometro(QWidget, PacientInterface):
    STARTED = 0
    STOPPED = ...
    END = ...
    # La parte int, la voy a dejar, pero no la usare.
    finishedSignal: pyqtSignal = pyqtSignal(Prueba, int)

    def pacientSelected(self, pacient, index):
        super().pacientSelected(pacient, index)
        self.start_and_lap.setEnabled(True)

    def __init__(self, user: str, parent=None):
        super(Cronometro, self).__init__(parent)
        self.user = user
        self.settings: UserSettings = UserSettings(user)
        PacientInterface.__init__(self)
        get_cronometro_widget_ui(self)
        self.formLayout: QFormLayout = self.formLayout
        self.vuelta3_label: QLabel = self.vuelta3_label
        self.vuelta2_label: QLabel = self.vuelta2_label
        self.vuelta1_label: QLabel = self.vuelta1_label
        self.vuelta3_edit: QTextEdit = self.vuelta3_edit
        self.vuelta2_edit: QTextEdit = self.vuelta2_edit
        self.vuelta1_edit: QTextEdit = self.vuelta1_edit
        self.setObjectName("cronometro_paciente")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.progress_bar = get_cronometro_bar_widget()
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Le ponemos los colores y los maximos al cronometro

        # editamos los label con los ajustes
        self.vuelta1_label.setText(self.settings.value(self.settings.LAP0_NAME))
        self.vuelta2_label.setText(self.settings.value(self.settings.LAP1_NAME))
        self.vuelta3_label.setText(self.settings.value(self.settings.LAP2_NAME))
        self.crono_widget.addWidget(self.progress_bar)
        self.stop_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.prueba_actual: Prueba = ...
        # Conexiones de los botones
        self.start_and_lap.clicked.connect(self.start_and_lap_slot)
        self.cancel_button.clicked.connect(self.cancel_slot)
        self.stop_button.clicked.connect(self.stop_slot)
        ###################################################################
        # Configuracion progress bar
        # self.start_and_lap.setEnabled(True)
        self.timer = None
        self.laps = []
        self.STOPPED = 3
        self.END = self.STOPPED - 1
        self.status = self.STOPPED
        self.set_to_actual_state()

    def start_and_lap_slot(self):
        from main_window import UI
        if self.status == self.STOPPED:
            self.sender().emit_again = True
            self.status = self.STARTED
            self.timer = Timer()

            self.prueba_actual = Prueba(pacient_id=self.pacient.dni,
                                        datetime_of_test=datetime.datetime.now(),
                                        laps=self.timer.laps)

            self.timer.signaler.on_progress.connect(self.on_progress)
            UI.threadpool.start(self.timer)
            self.stop_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        elif self.status == self.END:  # A acabado el ciclo.
            self.stop_slot()
            self.timer.lap()
            self.status = self.STOPPED
            self.cancel_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.prueba_actual.notas = [self.vuelta1_edit.toPlainText(),
                                  self.vuelta2_edit.toPlainText(),
                                  self.vuelta3_edit.toPlainText()]
            self.finishedSignal.emit(self.prueba_actual, self.index)
        else:  # Esta en ciclo.
            lap = self.timer.lap()
            self.status += 1
        self.set_to_actual_state()

    def set_to_actual_state(self):
        if self.status != self.STOPPED:
            string = self.settings.get_lap_name(self.status)
            button_string = "Actual: " + string
            self.progress_bar.setMaximun(self.settings.get_lap_time(self.status, 1))
            self.progress_bar.changeYellowThereshold(self.settings.get_lap_time(self.status, 0))
        else:
            button_string = "Empezar"
        self.start_and_lap.setText(button_string)

    def stop_slot(self):  # Paras el timer
        if self.status != self.STOPPED and self.timer is not None:
            self.cancel_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.timer.stop()
            self.status = self.STOPPED


    def cancel_slot(self):  # Reseteas el timer
        self.stop_slot()
        self.timer = None
        self.progress_bar.setValue(datetime.timedelta(seconds=0))

    def on_progress(self, timdelta: datetime.timedelta):
        self.sender().emit_again = False
        self.progress_bar.setValue(timdelta)
        self.statusChangeSlot.emit(f"{self.prueba_actual}", 1)
        self.sender().emit_again = True

    def init(self):
        super().init()