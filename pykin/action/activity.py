import numpy as np
from abc import abstractclassmethod, ABCMeta
from dataclasses import dataclass

import pykin.utils.plot_utils as plt
from pykin.scene.scene import SceneManager
from pykin.utils.action_utils import surface_sampling
from pykin.planners.cartesian_planner import CartesianPlanner
from pykin.planners.rrt_star_planner import RRTStarPlanner

@dataclass
class ActionInfo:
    ACTION = "action"
    PICK_OBJ_NAME = "pick_obj_name"
    HELD_OBJ_NAME = "held_obj_name"
    PLACE_OBJ_NAME = "place_obj_name"
    GRASP_POSES = "grasp_poses"
    PRE_GRASP_POSES = "pre_grasp_poses"
    POST_GRASP_POSES = "post_grasp_poses"
    TCP_POSES = "tcp_poses"
    RELEASE_POSES = "release_poses"
    LEVEL = "level"
    
class ActivityBase(metaclass=ABCMeta):
    """
    Activity Base class

    Args:
        robot (SingleArm or Bimanual): manipulator type
        robot_col_mngr (CollisionManager): robot's CollisionManager
        object_mngr (ObjectManager): object's Manager
    """
    def __init__(
        self,
        scene_mngr:SceneManager,
        retreat_distance=0.1
    ):
        self.scene_mngr = scene_mngr.copy_scene(scene_mngr)
        self.retreat_distance = retreat_distance
        self.action_info = ActionInfo

        # Add Planner
        self.cartesian_planner = CartesianPlanner()
        self.rrt_planner = RRTStarPlanner(delta_distance=0.08, epsilon=0.2, gamma_RRT_star=1.5)

    def __repr__(self) -> str:
        return 'pykin.action.activity.{}()'.format(type(self).__name__)

    @abstractclassmethod
    def get_possible_actions_level_1(self):
        raise NotImplementedError

    @abstractclassmethod
    def get_possible_ik_solve_level_2(self):
        raise NotImplementedError

    @abstractclassmethod
    def get_possible_joint_path_level_3(self):
        raise NotImplementedError

    @abstractclassmethod
    def get_possible_transitions(self):
        raise NotImplementedError

    def get_surface_points_from_mesh(self, mesh, n_sampling=100, weights=None):
        contact_points, _, normals = surface_sampling(mesh, n_sampling, weights)
        return contact_points, normals

    def _collide(self, is_only_gripper:bool)->bool:
        collide = False
        # self.scene_mngr.robot_collision_mngr.show_collision_info()
        # self.scene_mngr.obj_collision_mngr.show_collision_info()
        if is_only_gripper:
            collide = self.scene_mngr.collide_objs_and_gripper()
        else:
            collide = self.scene_mngr.collide_objs_and_robot()
        return collide

    def _solve_ik(self, pose1, pose2, eps=1e-3):
        pose_error = self.scene_mngr.scene.robot.get_pose_error(pose1, pose2)
        if pose_error < eps:
            return True
        return False

    def _check_stability(self):
        pass
    
    def _check_com(self):
        pass

    def get_cartesian_path(self, cur_q, goal_pose, n_step=50):
        self.cartesian_planner._n_step = n_step
        self.cartesian_planner.run(self.scene_mngr, cur_q, goal_pose, collision_check=False)
        return self.cartesian_planner.get_joint_path()

    def get_rrt_star_path(self, cur_q, goal_pose, max_iter=500, n_step=30):
        self.rrt_planner.run(self.scene_mngr, cur_q, goal_pose, max_iter)
        return self.rrt_planner.get_joint_path(n_step=n_step)

    def show(self):
        self.scene_mngr.show()