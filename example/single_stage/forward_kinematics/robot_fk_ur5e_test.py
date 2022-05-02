import numpy as np
import sys, os

pykin_path = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(pykin_path)
from pykin.kinematics.transform import Transform
from pykin.robots.single_arm import SingleArm
from pykin.utils import plot_utils as plt

file_path = '../../../asset/urdf/ur5e/ur5e.urdf'
robot = SingleArm(file_path, Transform(rot=[0.0, 0.0, 0.0], pos=[0, 0, 0]))
robot.setup_link_name("ur5e_base_link", "ur5e_right_hand")

target_thetas = [-0.470, -1.735, 2.480, -2.275, -1.590, -1.991]
robot.set_transform(target_thetas)

_, ax = plt.init_3d_figure("FK")
plt.plot_robot(ax=ax, 
               robot=robot,
               geom="visual",
               only_visible_geom=False,
               alpha=0.5)
plt.show_figure()
