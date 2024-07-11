#!/usr/bin/env python3

from typing import Dict

import numpy as np
from sensor_calibration_manager.calibrator_base import CalibratorBase
from sensor_calibration_manager.calibrator_registry import CalibratorRegistry
from sensor_calibration_manager.ros_interface import RosInterface
from sensor_calibration_manager.types import FramePair


@CalibratorRegistry.register_calibrator(
    project_name="lxo", calibrator_name="camera_lidar_tag_based_pnp_calibrator"
)
class CameraLidarTagBasedPNPCalibrator(CalibratorBase):
    required_frames = []

    def __init__(self, ros_interface: RosInterface, **kwargs):
        super().__init__(ros_interface)

        self.cam_name = kwargs["camera_name"]
        self.lidar_frame = kwargs["lidar_frame"]
        self.roof_datum = "vehicle_roof_datum"

        self.required_frames.extend(
            [
                self.roof_datum,
                self.lidar_frame,
                f'camera_{self.cam_name}_mount',
                f'camera_{self.cam_name}_sensor',
                f'camera_{self.cam_name}_optical',
            ]
        )
        # self.required_frames.append(f'camera_{self.cam_name}_optical')
        # self.required_frames.append(self.lidar_frame)

        # vehicle_roof_datum
        #   lidar_ouster_top
        #   camera_fsp_l_mount
        #       camera_fsp_l_sensor
        #           camera_fsp_l_optical
        self.add_calibrator(
            service_name="calibrate_camera_lidar",
            expected_calibration_frames=[
                FramePair(parent=f'camera_{self.cam_name}_optical', child=self.lidar_frame),
            ],
        )

    # def post_process(self, calibration_transforms: Dict[str, Dict[str, np.array]]):
    #     optical_link_to_lidar_transform = calibration_transforms[
    #         f"{self.camera_name}/camera_optical_link"
    #     ][self.lidar_frame]

    #     sensor_kit_to_lidar_transform = self.get_transform_matrix(
    #         self.sensor_kit_frame, self.lidar_frame
    #     )

    #     camera_to_optical_link_transform = self.get_transform_matrix(
    #         f"{self.camera_name}/camera_link", f"{self.camera_name}/camera_optical_link"
    #     )

    #     sensor_kit_camera_link_transform = np.linalg.inv(
    #         camera_to_optical_link_transform
    #         @ optical_link_to_lidar_transform
    #         @ np.linalg.inv(sensor_kit_to_lidar_transform)
    #     )

    #     result = {
    #         self.sensor_kit_frame: {
    #             f"{self.camera_name}/camera_link": sensor_kit_camera_link_transform
    #         }
    #     }
    #     return result
