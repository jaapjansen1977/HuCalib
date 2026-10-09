"""Import the original synchronized demo at its original FPS and analyse it.

This creates a new test session; it does not relabel encoder test recordings as
scientific input or change the official calibration's known width mismatch.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2

from mocap_app.analysis.pose2sim import run_analysis
from mocap_app.io.recording_session import RecordingSession
from mocap_app.models.types import CameraSourceConfig


def import_demo(demo: Path, calibration: Path, output: Path) -> None:
    originals = sorted((demo / 'videos').glob('*.mp4'))
    if len(originals) != 4:
        raise ValueError('Expected four official single-person demo videos')
    tables = tomllib.loads(calibration.read_text(encoding='utf-8'))
    payload = {'cameras': {}}
    for video in originals:
        table = next(t for k, t in tables.items() if k != 'metadata' and t['name'] == video.stem)
        payload['cameras'][video.stem] = {
            'source_id': video.stem, 'intrinsics': table['matrix'], 'distortion': table['distortions'],
            'rotation': table['rotation'], 'translation': table['translation'], 'image_size': table['size'],
        }
    output.mkdir(parents=True, exist_ok=False)
    session = RecordingSession(output, 60, {},
        [CameraSourceConfig(v.stem, 'video', str(v)) for v in originals], payload)
    session.manifest['import_provenance'] = {
        'kind': 'official_pose2sim_demo', 'original_fps_preserved': True,
        'synchronization': 'assumed_from_official_demo',
        'timestamps': 'media timeline, not host acquisition or sensor exposure',
    }
    try:
        for video in originals:
            destination = output / video.name
            shutil.copy2(video, destination)
            capture = cv2.VideoCapture(str(destination))
            try:
                fps = capture.get(cv2.CAP_PROP_FPS)
                index = 0
                while True:
                    ok, image = capture.read()
                    if not ok:
                        break
                    index += 1
                    if index == 1:
                        session.video_opened(video.stem, destination, (image.shape[1], image.shape[0]), fps)
                    session.event({'camera_id': video.stem, 'batch_id': f'demo_{index}',
                        'batch_index': index, 'capture_batch_index': None, 'source_frame_index': index,
                        'timestamp_kind': 'media_timeline', 'timestamp_media_sec': (index - 1) / fps,
                        'timestamp_monotonic_ns': None}, 'written', video_frame_index=index)
            finally:
                capture.release()
    finally:
        session.finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--assume-synchronized', action='store_true')
    args = parser.parse_args()
    import_demo(args.demo, args.calibration, args.session)
    report = run_analysis(args.session, args.output, args.demo / 'Config.toml', args.python,
                          diagnostic_resolution_mismatch=True, assume_synchronized=args.assume_synchronized)
    assert report['status'] == 'completed'
    assert len(report['inputs']) == 4
    assert all(v['decoded_frames'] == 100 and abs(v['fps'] - 60) < .01 for v in report['inputs'])
    print(json.dumps({'status': report['status'], 'stages': report['stages'],
                      'artifacts': report['artifacts'], 'warnings': report['warnings']}, indent=2))


if __name__ == '__main__':
    main()
