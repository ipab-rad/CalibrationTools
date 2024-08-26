#!/usr/bin/env python3

from typing import Dict

import numpy as np
import xml.etree.ElementTree as ET
from sensor_calibration_manager.calibrator_base import CalibratorBase
from sensor_calibration_manager.calibrator_registry import CalibratorRegistry
from sensor_calibration_manager.ros_interface import RosInterface
from sensor_calibration_manager.types import FramePair
from scipy.spatial.transform import Rotation as R

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
    
        # Print XML xacro macro
        self.print_xacro_macro_xml(camera_sensor_to_camera_optical_transform,
                                   f'camera_{self.cam_name}_sensor',
                                   f'camera_{self.cam_name}_optical')
        
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
    
    def print_xacro_macro_xml(self, transform, parent, child):
        
        # Create the root element
        camera_mount_tree = ET.Element("xacro:camera_mount", name=child, parent=parent)
        # Extract xyz and rpy
        xyz, rpy = self.extract_xyz_rpy_str(transform)
        
        # Create the origin element and set its attributes
        origin = ET.SubElement(camera_mount_tree, "origin", xyz=xyz, rpy=rpy)

        # Indent tree
        self.indent(camera_mount_tree)
        
        # Convert the ElementTree to a string
        camera_mount_xml = ET.tostring(camera_mount_tree, encoding='unicode', method='xml')

        # Define the ANSI escape codes for colors
        BRIGHT_WHITE = '\033[97m'
        BRIGHT_GREEN = '\033[92m'
        BRIGHT_CYAN = '\033[96m'
        RESET = '\033[0m'

        # Print the XML string
        print(f'\n{BRIGHT_GREEN}Transformation from {BRIGHT_WHITE}{parent} {BRIGHT_GREEN}'
            f'to {BRIGHT_WHITE}{child} {BRIGHT_GREEN}has been computed.\n'
            f'Please add the following XML snippet to the file:\n'
            f'av_car_description/urdf/mondeo_dca/mondeo_dca_sensors.xacro\n'
            f'{BRIGHT_CYAN}{camera_mount_xml}{RESET}')
    
    def extract_xyz_rpy_str(self, T):
        # Extract translation
        translation = T[:3, 3]
        xyz = " ".join(f"{val:.6g}" for val in translation)
        
        # Extract rotation and convert to rpy
        rotation_matrix = T[:3, :3]
        r = R.from_matrix(rotation_matrix)
        rpy = r.as_euler('xyz', degrees=False)  # Roll, pitch, yaw in radians
        rpy_str = " ".join(f"{val:.6g}" for val in rpy)
        
        return xyz, rpy_str
    
    def indent(self, elem, level=0):
        # Add indentation
        indent_size = "  "
        i = "\n" + level * indent_size
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_size
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
        