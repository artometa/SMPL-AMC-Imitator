import numpy as np
import transforms3d


smpl_keypoint_semantic = {
  0: 'root',
  1: 'llegroot',
  2: 'rlegroot',
  3: 'lowerback',
  4: 'lknee',
  5: 'rknee',
  6: 'upperback',
  7: 'lankle',
  8: 'rankle',
  9: 'thorax',
  10: 'ltoes',
  11: 'rtoes',
  12: 'lowerneck',
  13: 'lclavicle',
  14: 'rclavicle',
  15: 'upperneck',
  16: 'larmroot',
  17: 'rarmroot',
  18: 'lelbow',
  19: 'relbow',
  20: 'lwrist',
  21: 'rwrist',
  22: 'lhand',
  23: 'rhand'
}


smpl_asf_map = {
  0: 'root',
  1: 'lfemur',
  2: 'rfemur',
  3: 'upperback',
  4: 'ltibia',
  5: 'rtibia',
  6: 'thorax',
  7: 'lfoot',
  8: 'rfoot',
  9: 'lowerneck',
  10: 'ltoes',
  11: 'rtoes',
  12: 'upperneck',
  13: 'lclavicle',
  14: 'rclavicle',
  15: 'head',
  16: 'lhumerus',
  17: 'rhumerus',
  18: 'lradius',
  19: 'rradius',
  20: 'lwrist',
  21: 'rwrist',
  22: 'lhand',
  23: 'rhand'
}

asf_smpl_map = {
  'root': 0,
  'lfemur': 1,
  'rfemur': 2,
  'upperback': 3,
  'ltibia': 4,
  'rtibia': 5,
  'thorax': 6,
  'lfoot': 7,
  'rfoot': 8,
  'lowerneck': 9,
  'ltoes': 10,
  'rtoes': 11,
  'upperneck': 12,
  'lclavicle': 13,
  'rclavicle': 14,
  'head': 15,
  'lhumerus': 16,
  'rhumerus': 17,
  'lradius': 18,
  'rradius': 19,
  'lwrist': 20,
  'rwrist': 21,
  'lhand': 22,
  'rhand': 23
}

class Joint:
  def __init__(self, name, direction, length, axis, dof, limits):
    self.name = name
    self.direction = np.matrix(direction)
    self.length = length
    axis = np.deg2rad(axis)
    self.C = np.matrix(transforms3d.euler.euler2mat(*axis))
    self.Cinv = np.linalg.inv(self.C)
    self.limits = np.zeros([3, 2])
    self.movable = len(dof) == 0
    for lm, nm in zip(limits, dof):
      if nm == 'rx':
        self.limits[0] = lm
      elif nm == 'ry':
        self.limits[1] = lm
      else:
        self.limits[2] = lm
    self.parent = None
    self.children = []
    # bone's far end's cooridnate
    # near end is parent's end_coord
    self.end_coord = None
    self.matrix = None

  def set_motion(self, motion):
    if self.name == 'root':
      self.end_coord = np.array(motion['root'][:3])
      self.end_coord = np.zeros(3)
      rotation = np.deg2rad(motion['root'][3:])
      self.matrix = self.C * np.matrix(transforms3d.euler.euler2mat(*rotation)) * self.Cinv
    else:
      # set rx ry rz according to degree of freedom
      idx = 0
      rotation = np.zeros(3)
      for axis, lm in enumerate(self.limits):
        if not np.array_equal(lm, np.zeros(2)):
          rotation[axis] = motion[self.name][idx]
          idx += 1
      rotation = np.deg2rad(rotation)
      self.matrix = self.parent.matrix * self.C * \
          np.matrix(transforms3d.euler.euler2mat(*rotation)) * self.Cinv
      self.end_coord = np.squeeze(np.array(np.reshape(self.parent.end_coord, [3, 1]) + self.length * self.matrix * np.reshape(self.direction, [3, 1])))

      if self.name == 'ltibia':
        print('================== ASF ltibia =================')
        print(np.array(self.matrix * np.reshape(self.direction, [3, 1])))

    for child in self.children:
      child.set_motion(motion)

  def to_dict(self):
    ret = {self.name: self}
    for child in self.children:
      ret.update(child.to_dict())
    return ret

  def reset_pose(self):
    if self.name == 'root':
      self.end_coord = np.zeros(3)
    else:
      self.end_coord = self.parent.end_coord + self.length * self.direction
    for child in self.children:
      child.reset_pose()

  def pretty_print(self):
    print('===================================')
    print('joint: %s' % self.name)
    print('direction:')
    print(self.direction)
    print('limits:', self.limits)
    print('parent:', self.parent)
    print('children:', self.children)


class SMPLJoints:
  def __init__(self, idx):
    self.idx = idx
    self.to_parent = None
    self.parent = None
    self.coordinate = None
    self.matrix = None
    self.children = []

  def init_bone(self):
    if self.parent is not None:
      self.to_parent = self.coordinate - self.parent.coordinate

  def set_motion(self, R):
    if self.parent is not None:
      self.coordinate = self.parent.coordinate + \
          np.squeeze(np.dot(self.parent.matrix,
                            np.reshape(self.to_parent, [3, 1])))
      self.matrix = np.dot(self.parent.matrix, R[self.idx])
    else:
      self.matrix = R[self.idx]

    if self.idx == asf_smpl_map['lfemur']:
      print('====================== SMPL =====================')
      print(self.to_parent / np.linalg.norm(self.to_parent))
      print(self.matrix)
      print(np.squeeze(np.dot(self.parent.matrix, np.reshape(self.to_parent, [3, 1]))))

    for child in self.children:
      child.set_motion(R)

  def to_dict(self):
    ret = {self.idx: self}
    for child in self.children:
      ret.update(child.to_dict())
    return ret
