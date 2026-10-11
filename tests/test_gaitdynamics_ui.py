from pathlib import Path
import tempfile
import unittest

from PySide6.QtWidgets import QApplication
from mocap_app.ui.gaitdynamics_dialog import GaitDynamicsDialog


class GaitDynamicsUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_incompatible_pose2sim_input_can_be_reported_without_ai_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            motion, model = root / 'example.mot', root / 'model.osim'
            motion.write_text('nRows=2\nnColumns=2\ninDegrees=yes\nendheader\ntime knee_angle_r\n0 10\n.1 20\n')
            model.write_text('<OpenSimDocument><Model><JointSet/></Model></OpenSimDocument>')
            dialog = GaitDynamicsDialog(motion, model)
            self.addCleanup(dialog.deleteLater)
            dialog._check()
            self.assertFalse(dialog.report['compatible'])
            self.assertTrue(dialog.save_button.isEnabled())
            self.assertIn('nog niet geschikt', dialog.details.toPlainText())
            self.assertIn('lumbar', dialog.details.toPlainText())
            dialog.motion.setText(str(root / 'different.mot'))
            self.assertIsNone(dialog.report)
            self.assertFalse(dialog.save_button.isEnabled())


if __name__ == '__main__':
    unittest.main()
