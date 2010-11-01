#!/usr/bin/python 
import epics
import time
import debugtime

params = {'Shutter':        'eps_mbbi4',
          'pitchFB_ON':     'mono_pid1.FBON',
          'pitchFB_Locked': 'mono_pid1Locked',
          'pitchFB_Reset':  'mono_pid1EnableReset' ,
          'i0_setpoint':    'mono_pid1.VAL',
          'i0_actual':      'mono_pid1.CVAL',
          'tilt_coarsee':    'm12.VAL',
          'tilt_fine':      'DAC1_3.VAL',
          'roll_fine':      'DAC1_2.VAL',
          'roll_tweakval':  'm11.TWV',
          'roll_twf':       'm11.TWF',
          'roll_twr':       'm11.TWR',
          'preslit_sum':    'mono_pid2_incalc.M',
          'preslit_diff':   'mono_pid2_incalc.N',
          }

class mono_control(epics.Device):
    """  mono control and feedback
    """
    MAX_DIFF = 0.25
    MIN_SUM  = 0.1

    def __init__(self, prefix):
        self._prefix = prefix
        epics.Device.__init__(self, self._prefix)
        for key, val in params.items():
            self.add_pv("%s%s" % (self._prefix, val), attr=key)
        
    def OptimizeMonoRoll(self):
        self.FeedbackOff()
        self.roll_fine = 0
        print 'July2010: Check Mono Roll: Split Sum / Diff ', self.preslit_sum, self.preslit_diff

        if self.preslit_diff <= self.MIN_SUM:
            print '   pre-slit intensity too low -- beam lost?? ', self.preslit_sum
            return
        elif abs(self.preslit_diff) < self.MAX_DIFF:
            return
        rcount = 0
        print 'pre-slit needs roll adjustment'
        self.roll_tweakval = 0.0005
        while rcount < 20  and (abs(self.preslit_diff) > self.MAX_DIFF/2.0):
            rcount = rcount + 1
            if split_diff < 0:
                self.roll_twr = 1
            else:
                self.roll_twf = 1                
            print 'pre-slit diff, sum = ', self.preslit_diff, self.preslit_sum, rcount
            time.sleep(0.5)
        print 'pre-slit roll adjustment finished in ' , rcount, ' steps.'
        return

    def WaitForShutterOpen(self, timeout=600):
        t0 = time.time()
        while self.Shutter != 1:
            epics.ca.poll()
            if time.time() - t0 > timeout:
                break
            time.sleep(0.1)
        return self.Shutter == 1

    def FeedbackOn(self):
        self.pitchFB_ON =  1
        self.pitchFB_Reset = 1

    def FeedbackOff(self):
        self.pitchFB_ON = 0

    def FeedbackResetOff(self):
        self.pitchFB_Reset = 0

    def WaitForFeedbackLocked(self,timeout=1800):
        self.FeedbackOn()
        t0 = time.time()
        while self.pitchFB_Locked != 1:
            epics.ca.poll()
            if time.time() - t0 > timeout:
                break
            time.sleep(0.1)
        print 'Feedback locked! '
        return  self.pitchFB_Locked == 1
        
    def CheckMonoPitch(self):
        if abs(self.tilt_fine) < 2.0:
            print 'Mono tilt fine adjust looks OK'
        else:
            self.OptimizeMonoPitch()
        self.OptimizeMonoRoll()
        self.FeedbackOn()

    def OptimizeMonoPitch(self):
        print 'Need to Optimize Mono Pitch: '
        self.FeedbackOff()
        self.FeedbackResetOff()

        self.tilt_fine = 0
        # 
        i0max = -1.0
        fine_val = -1.0
        for i in range(80):
            fine_val = -4.0 + i * 0.1
            self.tilt_fine = fine_val
            time.sleep(0.1)
            if self.i0_actual > i0max:
                i0max = self.i0_actual
                fine_best = fine_val
            if i0max > 1.25 * self.i0_setpoint:
                print 'no need for full search '
                self.tilt_fine = -3.5
                time.sleep(0.1)
                self.tilt_fine =  fine_best-0.5
                self.FeedbackOn()
                return self.WaitForFeedbackLocked()
                
        # search with coarse tilt and presilt
        tilt_coarse0 = coarse_best =self.tilt_coarsee
        print 'Starting Coarse Val = ', tilt_coarse0
        self.tilt_fine = 0
        for step in (8e-4, 2.e-4):
            summax = 0
            for i in range(40):
                coarse_val = coarse_best - (i-20) * step
                self.tilt_coarsee = coarse_val
                time.sleep(0.1)
                if self.preslit_sum > summax and (self.i0_actual > 0.1*self.i0_setpoint):
                    summax = self.preslit_sum
                    coarse_best = coarse_val
                    print 'see max Sum at ', coarse_best

            print 'step size %.5f -> coarse_best=%f' % (step,coarse_best)
        self.tilt_coarsee = coarse_best
        self.tilt_fine =  -1.5
        self.FeedbackOn()
        return self.WaitForFeedbackLocked()        

    
if __name__ == '__main__':
    m = mono_control('13IDA:')
    
    time.sleep(0.1)
    x = m.WaitForShutterOpen()
    x = m.WaitForFeedbackLocked()
    print x
