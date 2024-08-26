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
        
        self.add_calibrator(
            service_name="calibrate_camera_lidar",
            expected_calibration_frames=[
                FramePair(parent=f'camera_{self.cam_name}_optical', child=self.lidar_frame),
            ],
        )

    def post_process(self, calibration_transforms: Dict[str, Dict[str, np.array]]):
        
        # Get camera optical -> lidar tf from the calibration result
        optical_link_to_lidar_transform = calibration_transforms[
            f"camera_{self.cam_name}_optical"
        ][self.lidar_frame]
    
        # Invert calibration result to get lidar -> camera_optical
        lidar_to_optical_link_transform = np.linalg.inv(optical_link_to_lidar_transform)

        # Get camera_sensor -> lidar_frame transform from ROS2 TF
        camera_sensor_to_lidar_transform = self.get_transform_matrix(
            f'camera_{self.cam_name}_mount',  self.lidar_frame
        )
        
        # Compute camera_sensor -> camera_optical 
        camera_sensor_to_camera_optical_transform = camera_sensor_to_lidar_transform@lidar_to_optical_link_transform
    
        # Set results TF dictionary
        result = {
            f'camera_{self.cam_name}_sensor': {
                f'camera_{self.cam_name}_optical': camera_sensor_to_camera_optical_transform
            },
            f'camera_{self.cam_name}_optical': {
                f'{self.lidar_frame}': optical_link_to_lidar_transform
            }
        }
        
        return result
