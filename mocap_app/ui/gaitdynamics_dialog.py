"""Inspect Pose2Sim/OpenSim inputs before optional GaitDynamics processing."""
import json
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout)

from mocap_app.analysis.gaitdynamics import inspect_inputs
from mocap_app.core.branding import APP_NAME
from mocap_app.ui.window_geometry import fit_window_to_screen


class GaitDynamicsDialog(QDialog):
    def __init__(self, motion: Path | None, model: Path | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'GaitDynamics — {APP_NAME}')
        self.setMinimumSize(480, 340)
        self.report = None
        layout = QVBoxLayout(self)
        note = QLabel('Experimentele koppeling voor het voorspellen van grondreactiekrachten. '
            'De rekenmodule draait apart op Linux of WSL2 (Linux op Windows), met CPU-verwerking. '
            'Controleer eerst of het bewegingsbestand en het bijbehorende lichaamsmodel geschikt zijn.')
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.motion = self._file(form, 'Bewegingsbestand', motion, '*.mot')
        self.model = self._file(form, 'OpenSim-model', model, '*.osim')
        layout.addLayout(form)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText('De controle verandert geen opname, model of analyseresultaat.')
        layout.addWidget(self.details, 1)
        actions = QHBoxLayout()
        self.check_button = QPushButton('Invoer controleren')
        self.save_button = QPushButton('Rapport bewaren')
        close = QPushButton('Sluiten')
        for button in (self.check_button, self.save_button, close):
            actions.addWidget(button)
        layout.addLayout(actions)
        self.save_button.setEnabled(False)
        self.check_button.clicked.connect(self._check)
        self.save_button.clicked.connect(self._save)
        close.clicked.connect(self.close)
        self.motion.textChanged.connect(self._invalidate)
        self.model.textChanged.connect(self._invalidate)
        fit_window_to_screen(self, QSize(820, 560))

    def _file(self, form, label, value, pattern):
        row = QHBoxLayout()
        field = QLineEdit(str(value or ''))
        button = QPushButton('Kiezen…')
        row.addWidget(field, 1)
        row.addWidget(button)
        form.addRow(label, row)
        def choose():
            path = QFileDialog.getOpenFileName(self, label, field.text(), f'OpenSim ({pattern})')[0]
            if path:
                field.setText(path)
        button.clicked.connect(choose)
        return field

    def _invalidate(self):
        self.report = None
        self.save_button.setEnabled(False)

    def _check(self):
        try:
            self.report = inspect_inputs(Path(self.motion.text()), Path(self.model.text()))
            status = 'Invoer geschikt voor de afzonderlijke rekenmodule.' if self.report['compatible'] else 'Invoer nog niet geschikt voor GaitDynamics.'
            self.details.setPlainText(status + '\n\n' + '\n\n'.join(self.report['errors']) +
                f"\n\n{self.report['rows']} tijdstappen · {self.report['duration_seconds']:.2f} seconden\n" +
                'Voorspelde krachten zijn geen gemeten krachten. De meetnauwkeurigheid is niet gevalideerd.')
            self.save_button.setEnabled(True)
        except Exception as error:
            self.report = None
            self.save_button.setEnabled(False)
            self.details.setPlainText('Invoercontrole mislukt: ' + str(error))

    def _save(self):
        if self.report is None:
            return
        path = QFileDialog.getSaveFileName(self, 'Controlerapport bewaren', 'gaitdynamics-controle.json', 'JSON (*.json)')[0]
        if path:
            try:
                Path(path).write_text(json.dumps(self.report, indent=2), encoding='utf-8')
            except OSError as error:
                self.details.appendPlainText('Rapport kon niet worden bewaard: ' + str(error))
