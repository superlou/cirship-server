from oms.OMSimulator import OMSimulator
from time import time


class Simulation:
    def __init__(self, model_path):
        oms = OMSimulator('./temp')
        oms.newModel('model')
        oms.addSystem('model.root', oms.system_wc)  # WC for CS FMUs

        oms.addSubModel('model.root.system1', model_path)
        oms.setResultFile('model', '')
        oms.instantiate('model')
        oms.initialize('model')

        self.oms = oms
        self.start = time()

    def close(self):
        self.oms.terminate('model')
        self.oms.delete('model')

    def update(self):
        t = time() - self.start
        self.oms.stepUntil('model', t)
        return t

    def get_real(self, ref):
        return self.oms.getReal('model.root.system1.' + ref)[0]

    def get_bool(self, ref):
        return self.oms.getBoolean('model.root.system1.' + ref)[0]

    def set_real(self, ref, value):
        return self.oms.setReal('model.root.system1.' + ref, value)

    def set_bool(self, ref, value):
        return self.oms.setBoolean('model.root.system1.' + ref, value)

if __name__ == '__main__':
    sim = Simulation()
