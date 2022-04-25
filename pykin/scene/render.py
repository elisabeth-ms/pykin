import numpy as np
import trimesh
from abc import abstractclassmethod, ABCMeta

import pykin.utils.plot_utils as plt
from pykin.utils.kin_utils import apply_robot_to_scene, apply_objects_to_scene, apply_gripper_to_scene

class SceneRender(metaclass=ABCMeta):

    @abstractclassmethod
    def render_all_scene():
        raise NotImplementedError

    @abstractclassmethod
    def render_objects_and_gripper():
        raise NotImplementedError
    
    @abstractclassmethod
    def render_objects():
        raise NotImplementedError

    @abstractclassmethod
    def render_gripper():
        raise NotImplementedError

    @abstractclassmethod
    def show():
        raise NotImplementedError

class RenderTriMesh(SceneRender):

    def __init__(self):
        self.scene = trimesh.Scene()
    
    def render_all_scene(self, objs, robot, geom="collision"):
        self.render_objects(objs)
        self.render_robot(robot, geom)

    def render_objects_and_gripper(self, objs, robot):
        self.render_objects(objs)
        self.render_gripper(robot)

    def render_objects(self, objs):
        self.scene = apply_objects_to_scene(trimesh_scene=self.scene, objs=objs)

    def render_robot(self, robot, geom):
        self.scene = apply_robot_to_scene(trimesh_scene=self.scene, robot=robot, geom=geom)
        
    def render_gripper(self, robot):
        self.scene = apply_gripper_to_scene(trimesh_scene=self.scene, robot=robot)

    def show(self):
        self.scene.set_camera(np.array([np.pi/2, 0, np.pi/2]), 5, resolution=(1024, 512))
        self.scene.show('gl')
        self.scene = None

class RenderPyPlot(SceneRender):

    @staticmethod
    def render_all_scene(ax, objs, robot, alpha, robot_color, geom, visible_geom, visible_text):
        RenderPyPlot.render_objects(ax, objs, alpha)
        RenderPyPlot.render_robot(ax, robot, alpha, robot_color, geom, visible_geom, visible_text)

    @staticmethod
    def render_objects_and_gripper(ax, objs, robot, alpha, robot_color, visible_tcp):
        RenderPyPlot.render_objects(ax, objs, alpha)
        RenderPyPlot.render_gripper(ax, robot, alpha, robot_color, visible_tcp)

    @staticmethod
    def render_objects(ax, objs, alpha):
        plt.plot_objects(ax, objs, alpha)

    @staticmethod
    def render_robot(ax, robot, alpha, color, geom="collision", visible_geom=True, visible_text=True):
        plt.plot_robot(
            ax, 
            robot, 
            alpha=alpha, 
            color=color,
            geom=geom,
            visible_geom=visible_geom,
            visible_text=visible_text)

    @staticmethod
    def render_gripper(ax, robot, alpha=0.3, color=None, visible_tcp=True, pose=None):
        plt.plot_basis(ax)
        for link, info in robot.gripper.info.items():
            if info[1] == 'mesh':
                mesh_color = color
                if pose is None:
                    h_mat = info[3]
                else:
                    h_mat = pose
                print(h_mat)
                if color is None:
                    link = robot.links.get(link)
                
                    if link is not None:
                        mesh_color = link.collision.gparam.get('color')
                    else:
                        mesh_color = None

                    if mesh_color is None:
                        mesh_color = 'k'
                    else:
                        mesh_color = np.array([color for color in mesh_color.values()]).flatten()
                plt.plot_mesh(ax, mesh=info[2], h_mat=h_mat, alpha=alpha, color=mesh_color)

        if visible_tcp:
            ax.scatter(
                robot.gripper.info["tcp"][3][0,3], 
                robot.gripper.info["tcp"][3][1,3], 
                robot.gripper.info["tcp"][3][2,3], s=5, c='r')

    @staticmethod
    def render_trajectory(ax, poses):
        plt.plot_trajectories(ax, poses)

    @staticmethod
    def show():
        plt.show_figure()