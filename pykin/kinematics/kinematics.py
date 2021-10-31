import numpy as np
from collections import OrderedDict

from pykin.kinematics import jacobian as jac
from pykin.utils import transform_utils as tf
from pykin.utils.kin_utils import Baxter, calc_pose_error, convert_thetas_to_dict, logging_time

class Kinematics:
    """
    Class of Kinematics

    Args:
        robot_name (str): robot's name
        offset (Transform): robot's offset
        active_joint_names (list): robot's actuated joints
        base_name (str): reference link's name
        eef_name (str): end effector's name
    """
    def __init__(self, 
                robot_name, 
                offset, 
                active_joint_names=[],
                base_name="base", 
                eef_name=None, 
                ):
        self.robot_name = robot_name
        self.offset = offset
        self.active_joint_names = active_joint_names
        self.base_name = base_name
        self.eef_name = eef_name

    def forward_kinematics(self, frames, thetas):
        """
        Returns transformations obtained by computing fk

        Args:
            frames (list or Frame()): robot's frame for forward kinematics
            thetas (sequence of float): input joint angles

        Returns:
            transformations (OrderedDict): transformations
        """

        if not isinstance(frames, (list, dict)) :
            thetas = convert_thetas_to_dict(self.active_joint_names, thetas)
        transformations = self._compute_FK(frames, self.offset, thetas)
        return transformations
    
    @logging_time
    def inverse_kinematics(self, frames, current_joints, target_pose, method="LM", maxIter=1000):
        """
        Returns joint angles obtained by computing IK
        
        Args:
            frames (Frame()): robot's frame for invers kinematics
            current_joints (sequence of float): input joint angles
            target_pose (np.array): goal pose to achieve
            method (str): two methods to calculate IK (LM: Levenberg-marquardt, NR: Newton-raphson)
            maxIter (int): Maximum number of calculation iterations

        Returns:
            joints (np.array): target joint angles
        """
        if method == "NR":
            joints = self._compute_IK_NR(
                frames,
                current_joints, 
                target_pose, 
                maxIter=maxIter
            )
        if method == "LM":
            joints = self._compute_IK_LM(
                frames,
                current_joints, 
                target_pose, 
                maxIter=maxIter
            )
        return joints

    def _compute_FK(self, frames, offset, thetas):
        """
        Computes forward kinematics

        Args:
            frames (list or Frame()): robot's frame for forward kinematics
            offset (Transform): robot's offset
            thetas (sequence of float): input joint angles

        Returns:
            transformations (OrderedDict): transformations
        """
        transformations = OrderedDict()
        if not isinstance(frames, (list, dict)):
            trans = offset * frames.get_transform(thetas.get(frames.joint.name, 0.0))
            transformations[frames.link.name] = trans * frames.link.offset
            for child in frames.children:
                transformations.update(self._compute_FK(child, trans, thetas))
        else:
            # To compute IK
            cnt = 0
            trans = offset
            for frame in frames:
                trans = trans * frame.get_transform(thetas[cnt])
                transformations[frame.link.name] = trans * frame.link.offset
                if frame.joint.dtype != "fixed":
                    cnt += 1
                if cnt >= len(thetas):
                    cnt -= 1     
                if self.robot_name == "baxter":
                    Baxter.add_visual_link(transformations, frame)

        return transformations

    def _compute_IK_NR(self, frames, current_joints, target_pose, maxIter):
        """
        Computes inverse kinematics using newton raphson method

        Args:
            frames (list or Frame()): robot's frame for inverse kinematics
            current_joints (sequence of float): input joint angles
            target_pose (np.array): goal pose to achieve
            maxIter (int): Maximum number of calculation iterations

        Returns:
            joints (np.array): target joint angles
        """
        lamb = 0.5
        iterator = 0
        EPS = float(1e-6)
        dof = len(current_joints)

        target_pose = tf.get_homogeneous_matrix(target_pose[:3], target_pose[3:])

        cur_fk = self.forward_kinematics(frames, current_joints)
        cur_pose = list(cur_fk.values())[-1].homogeneous_matrix

        err_pose = calc_pose_error(target_pose, cur_pose, EPS)
        err = np.linalg.norm(err_pose)

        while err > EPS:

            iterator += 1
            if iterator > maxIter:
                break
            
            J = jac.calc_jacobian(frames, cur_fk, len(current_joints))
            dq = lamb * np.dot(np.linalg.pinv(J), err_pose)
            current_joints = [current_joints[i] + dq[i] for i in range(dof)]
            cur_fk = self.forward_kinematics(frames, current_joints)

            cur_pose = list(cur_fk.values())[-1].homogeneous_matrix
            err_pose = calc_pose_error(target_pose, cur_pose, EPS)
            err = np.linalg.norm(err_pose)

        print(f"Iterators : {iterator-1}")
        current_joints = np.array([float(current_joint) for current_joint in current_joints])
        return current_joints

    def _compute_IK_LM(self, frames, current_joints, target, maxIter):
        """
        Computes inverse kinematics using Levenberg-Marquatdt method

        Args:
            frames (list or Frame()): robot's frame for inverse kinematics
            current_joints (sequence of float): input joint angles
            target_pose (np.array): goal pose to achieve
            maxIter (int): Maximum number of calculation iterations

        Returns:
            joints (np.array): target joint angles
        """
        iterator = 0
        EPS = float(1E-12)
        dof = len(current_joints)
        wn_pos = 1/0.3
        wn_ang = 1/(2*np.pi)
        We = np.diag([wn_pos, wn_pos, wn_pos, wn_ang, wn_ang, wn_ang])
        Wn = np.eye(dof)

        target_pose = tf.get_homogeneous_matrix(target[:3], target[3:])

        cur_fk = self.forward_kinematics(frames, current_joints)
        cur_pose = list(cur_fk.values())[-1].homogeneous_matrix

        err = calc_pose_error(target_pose, cur_pose, EPS)
        Ek = float(np.dot(np.dot(err.T, We), err)[0])

        while Ek > EPS:
            iterator += 1
            if iterator > maxIter:
                break
            
            lamb = Ek + 0.002

            J = jac.calc_jacobian(frames, cur_fk, len(current_joints))
            Jh = np.dot(np.dot(J.T, We), J) + np.dot(Wn, lamb)
            
            gerr = np.dot(np.dot(J.T, We), err)
            dq = np.dot(np.linalg.pinv(Jh), gerr)
            current_joints = [current_joints[i] + dq[i] for i in range(dof)]
           
            cur_fk = self.forward_kinematics(frames, current_joints)
            cur_pose = list(cur_fk.values())[-1].homogeneous_matrix
            err = calc_pose_error(target_pose, cur_pose, EPS)
            Ek2 = float(np.dot(np.dot(err.T, We), err)[0])
            
            if Ek2 < Ek:
                Ek = Ek2
            else:
                current_joints = [current_joints[i] - dq[i] for i in range(dof)]
                cur_fk = self.forward_kinematics(frames, current_joints)
                break
            
        print(f"Iterators : {iterator-1}")
        current_joints = np.array([float(current_joint) for current_joint in current_joints])
        return current_joints