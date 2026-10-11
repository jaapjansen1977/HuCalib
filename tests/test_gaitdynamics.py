from pathlib import Path
import tempfile
import unittest

from mocap_app.analysis.gaitdynamics import (COORDINATES, GaitDynamicsError,
    inspect_inputs, read_motion, run_analysis, verify_runtime)


class GaitDynamicsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.motion = self.root / 'motion.mot'
        self.model = self.root / 'model.osim'
        bodies = ('pelvis', 'femur_r', 'tibia_r', 'talus_r', 'calcn_r',
                  'femur_l', 'tibia_l', 'talus_l', 'calcn_l', 'torso')
        self.model.write_text('<OpenSimDocument><Model><BodySet><objects>' +
            ''.join(f'<Body name="{name}"/>' for name in bodies) + '</objects></BodySet><JointSet><objects><CustomJoint><coordinates>' +
            ''.join(f'<Coordinate name="{name}"/>' for name in COORDINATES) +
            '</coordinates></CustomJoint></objects></JointSet></Model></OpenSimDocument>')
        self.write_motion()

    def write_motion(self, names=COORDINATES, rows=200, irregular=False):
        self.motion.write_text(f'nRows={rows}\nnColumns={len(names)+1}\ninDegrees=yes\nendheader\n' +
            '\t'.join(('time', *names)) + '\n' + '\n'.join(
                '\t'.join((str(i * .01 + (.05 if irregular and i > 50 else 0)), *['0'] * len(names))) for i in range(rows)) + '\n')

    def test_full_inputs_are_checked_without_loading_ai_dependencies(self):
        report = inspect_inputs(self.motion, self.model)
        self.assertTrue(report['compatible'])
        self.assertAlmostEqual(report['sampling_rate'], 100)
        self.assertFalse(report['scientific_accuracy_validated'])

    def test_segmented_spine_is_not_silently_renamed(self):
        self.write_motion(names=COORDINATES[:20] + ('L5_S1_Flex_Ext', 'L5_S1_Lat_Bending', 'L5_S1_axial_rotation'))
        self.assertFalse(inspect_inputs(self.motion, self.model)['compatible'])
        before = self.motion.read_bytes()
        with self.assertRaisesRegex(GaitDynamicsError, 'lumbar'):
            run_analysis(self.motion, self.model, self.root / 'output', self.root / 'runtime', Path('python'), 1.75, 70, 0)
        self.assertEqual(self.motion.read_bytes(), before)
        self.assertFalse((self.root / 'output').exists())

    def test_pose2sim_model_with_additional_spine_coordinates_is_blocked(self):
        self.model.write_text(self.model.read_text().replace('</coordinates>', '<Coordinate name="L5_S1_Flex_Ext"/></coordinates>'))
        self.assertFalse(inspect_inputs(self.motion, self.model)['compatible'])

    def test_short_or_irregular_motion_is_blocked(self):
        self.write_motion(rows=100)
        self.assertFalse(inspect_inputs(self.motion, self.model)['compatible'])
        self.write_motion(irregular=True)
        self.assertFalse(inspect_inputs(self.motion, self.model)['compatible'])

    def test_unknown_units_nonfinite_and_incorrect_headers_are_rejected(self):
        self.motion.write_text(self.motion.read_text().replace('inDegrees=yes', 'inDegrees=unknown'))
        self.assertFalse(inspect_inputs(self.motion, self.model)['compatible'])
        self.write_motion()
        self.motion.write_text(self.motion.read_text().replace('nRows=200', 'nRows=1000'))
        with self.assertRaises(GaitDynamicsError):
            read_motion(self.motion)
        self.write_motion()
        self.motion.write_text(self.motion.read_text().replace('0.01', 'nan', 1))
        with self.assertRaises(GaitDynamicsError):
            read_motion(self.motion)

    def test_unverified_runtime_and_model_files_are_rejected(self):
        runtime = self.root / 'runtime'
        runtime.mkdir()
        (runtime / 'gait_dynamics.py').write_text('print("wrong code")')
        with self.assertRaises(GaitDynamicsError):
            verify_runtime(runtime)

    def test_anthropometrics_must_be_finite_and_explicit(self):
        with self.assertRaises(GaitDynamicsError):
            run_analysis(self.motion, self.model, self.root / 'output', self.root, Path('python'), 1.75, float('nan'), 0)


if __name__ == '__main__':
    unittest.main()
