# Adapted from ARCap: https://github.com/Ericcsr/ARCap
import socket
import time
from argparse import ArgumentParser

import numpy as np
import pybullet as pb
from ip_config import *
from quest_robot_module import (
    QuestLeftArmGripperNoRokokoModule,
    QuestRightArmLeapModule,
)
from scipy.spatial.transform import Rotation

from toddlerbot.manipulation.teleoperation.data_processing.rigid_body_sento import (
    create_primitive_shape,
)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--frequency", type=int, default=30)
    parser.add_argument("--handedness", type=str, default="left")
    args = parser.parse_args()
    c = pb.connect(pb.DIRECT)
    vis_sp = []
    c_code = c_code = [[1,0,0,1], [0,1,0,1], [0,0,1,1], [1,1,0,1]]
    for i in range(4):
        vis_sp.append(create_primitive_shape(pb, 0.1, pb.GEOM_SPHERE, [0.02], color=c_code[i]))
    if args.handedness == "right":
        quest = QuestRightArmLeapModule(VR_HOST, LOCAL_HOST, POSE_CMD_PORT, IK_RESULT_PORT, vis_sp=None)
    else:
        quest = QuestLeftArmGripperNoRokokoModule(VR_HOST, LOCAL_HOST, POSE_CMD_PORT, IK_RESULT_PORT, vis_sp=vis_sp)

    start_time = time.time()
    fps_counter = 0
    packet_counter = 0
    print("Initialization completed")
    current_ts = time.time()
    while True:
        now = time.time()
        # TODO: May cause communication issues, need to tune on AR side.
        if now - current_ts < 1 / args.frequency: 
            continue
        else:
            current_ts = now
        try:
            #left_positions, right_positions = rokoko.receive()
            
            #rokoko.send_joint_data(np.vstack([left_positions[:5], right_positions[:5]]))
            wrist, head_pose= quest.receive()
            print(wrist, head_pose)
           
            if wrist is not None:
                wrist_orn = Rotation.from_quat(wrist[1])
                wrist_pos = wrist[0]
                head_pos = head_pose[0]
                head_orn = Rotation.from_quat(head_pose[1])
                if args.handedness == "right":
                    hand_tip_pose = wrist_orn.apply(right_positions) + wrist_pos
                else:
                    hand_tip_pose = None
                    #hand_tip_pose = wrist_orn.apply(left_positions) + wrist_pos
                #hand_tip_pose[[0,1,2,3]] = hand_tip_pose[[1,2,3,0]]
                arm_q, hand_q, wrist_pos, wrist_orn = quest.solve_system_world(wrist_pos, wrist_orn, hand_tip_pose)
                action = quest.send_ik_result(arm_q, hand_q)
                if quest.data_dir is not None:
                    if args.handedness == "right":
                        np.savez(f"{quest.data_dir}/right_data_{time.time()}.npz", right_wrist_pos=wrist_pos, right_wrist_orn=wrist_orn, 
                                                                                head_pos=head_pos, head_orn=head_orn.as_quat(),
                                                                                right_arm_q=arm_q, right_hand_q=action,raw_hand_q=hand_q,
                                                                                right_tip_poses=hand_tip_pose, point_cloud=point_cloud)
                    else:
                        np.savez(f"{quest.data_dir}/left_data_{time.time()}.npz", left_wrist_pos=wrist_pos, left_wrist_orn=wrist_orn, 
                                                                                head_pos=head_pos, head_orn=head_orn.as_quat(),
                                                                                left_arm_q=arm_q, left_hand_q=action, raw_hand_q=hand_q,
                                                                                left_tip_poses=hand_tip_pose, point_cloud=point_cloud)
        except socket.error as e:
            print(e)
            pass
        except KeyboardInterrupt:
            quest.close()
            break
        else:
            packet_time = time.time()
            fps_counter += 1
            packet_counter += 1

            if (packet_time - start_time) > 1.0:
                print(f"received {fps_counter} packets in a second", end="\r")
                start_time += 1.0
                fps_counter = 0
        

