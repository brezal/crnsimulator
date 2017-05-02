
import os
import imp
import unittest
from argparse import ArgumentParser

from crnsimulator.reactiongraph import ReactionGraph, ReactionNode
from crnsimulator.crn_parser import parse_crn_string
from crnsimulator.odelib_template import add_integrator_args


class testSolver(unittest.TestCase):
  def setUp(self):
    parser = ArgumentParser()
    add_integrator_args(parser)
    self.args = parser.parse_args([])
    self.filename = 'test_file.py'
    self.executable = 'test_file.pyc'

  def tearDown(self):
    ReactionNode.rid = 0
    os.remove(self.filename)
    os.remove(self.executable)

  def test_crn(self):
    # At some pont the simulator had troubles with CRNs that have
    # only one species...
    crn = "2X <=> 3X; X -> [k=0.1]"
    crn, _ = parse_crn_string(crn, process=True)

    # Split CRN into irreversible reactions
    new = []
    for [r, p, k] in crn :
      if None in k :
        k[:] = [x if x != None else 1 for x in k]
      if len(k) == 2:
        new.append([r,p,k[0]])
        new.append([p,r,k[1]])
      else :
        new.append([r,p,k[0]])
    crn = new

    RG = ReactionGraph(crn)

    filename, odename = RG.write_ODE_lib(filename=self.filename)
    _temp = imp.load_source(odename, filename)
    integrate = getattr(_temp, 'integrate')

    self.args.p0 = ['1=0.5']
    self.args.t_log = 10
    self.args.t0 = 0.1
    self.args.t8 = 10
    simu = integrate(self.args)

    first = simu[0]
    last = simu[-1]

    self.assertEqual(first, (0.10000000000000001, 0.5))
    self.assertEqual(last, (10.0, 0.88535344232897151))

