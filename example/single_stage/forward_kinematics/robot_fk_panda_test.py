import numpy as np
import sys, os

pykin_path = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(pykin_path)
from pykin.kinematics.transform import Transform
from pykin.robots.single_arm import SingleArm
from pykin.utils import plot_utils as plt

file_path = '../../../asset/urdf/panda/panda.urdf'
robot = SingleArm(file_path, Transform(rot=[0.0, 0.0, 0.0], pos=[0, 0, 0]))
robot.setup_link_name(eef_name="panda_right_hand")

target_thetas = [0, 0.1963495375, 0.00, -2.616, 0.00, 2.9415926, 0.78539815]
robot.set_transform(target_thetas)

_, ax = plt.init_3d_figure("FK")
plt.plot_robot(ax=ax, 
               robot=robot,
               geom="collision",
               only_visible_geom=True,
               alpha=0.9)
plt.show_figure()
