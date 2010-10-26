#!/usr/bin/python 
import epics
import time
from util import debugtime

params = {'Shutter':  'eps_mbbi4',
          'PitchFB_ON':     'mono_pid1.FBON',
          'PitchFB_Locked': 'mono_pid1Locked',
          'PitchFB_Reset':  'mono_pid1EnableReset' ,
          'I0_Setpoint':    'mono_pid1.VAL',
          'I0_Actual':      'mono_pid1.CVAL',
          'Tilt_Coarse':    'm12.VAL',
          'Tilt_Fine':      'DAC1_3.VAL',
          'Roll_Fine':      'DAC1_2.VAL',
          'Roll_Tweakval':  'm11.TWV',
          'Roll_TweakF':    'm11.TWF',
          'Roll_TweakR':    'm11.TWR',
          'PreSlit_Sum':    'mono_pid2_incalc.M',
          'PreSlit_Diff':   'mono_pid2_incalc.N',
          }

class mono_control(epics.Device):
    """ 
    mono control and feedback
    """
    MAX_DIFF = 0.25
    MIN_SUM  = 0.1

    def __init__(self,prefix):
        attrs = params.values()
        epics.Device.__init__(self,prefix, attrs=attrs)
        
    def OptimizeMonoRoll(self):
        pv_diff = '13IDA:mono_pid2_incalc.N'
        pv_sum  = '13IDA:mono_pid2_incalc.M'
        self.FeedbackOff()
        self.putVal('Roll_Fine', 0)
        split_diff = self.getVal('PreSlit_Diff')
        split_sum  = self.getVal('PreSlit_Sum')
        print 'July2010: Check Mono Roll: Split Sum / Diff ', split_sum, split_diff

        if split_sum <= self.MIN_SUM:
            print '   pre-slit intensity too low -- beam lost?? ', split_sum
            return
        elif abs(split_diff) < self.MAX_DIFF:
            return
        rcount = 0
        print 'pre-slit needs roll adjustment'
        self.putVal('Roll_Tweakval', 0.0005)
        while rcount < 20  and (abs(split_diff) > self.MAX_DIFF/2.0):
            rcount = rcount + 1
            adjust_pv = 'Roll_TweakF'
            if split_diff < 0:
                adjust_pv = 'Roll_TweakR'
            self.putVal(adjust_pv, 1)
            split_diff = self.getVal('PreSlit_Diff')
            split_sum  = self.getVal('PreSlit_Sum')
            print 'pre-slit diff, sum = ', split_diff, split_sum, rcount
            time.sleep(0.5)
        print 'pre-slit roll adjustment finished in ' , rcount, ' steps.'
        return

    def WaitForShutterOpen(self,timeout=600):
        t0 = time.time()
        while self.getVal('Shutter') != 1:
            epics.ca.poll()
            if time.time() - t0 > timeout:
                break
            time.sleep(0.1)
        return  self.getVal('Shutter')==1

    def getVal(self,key,**kw):
        pvname = key
        if key in params: pvname = params[key]
        return self.get(pvname,**kw)

    def putVal(self,key,val,**kw):
        pvname = key
        if key in params: pvname = params[key]
        return self.put(pvname,val,**kw)
    
    def FeedbackOn(self):
        self.putVal('PitchFB_ON', 1) 
        self.putVal('PitchFB_Reset', 1)       

    def FeedbackOff(self):
        self.putVal('PitchFB_ON', 0)

    def FeedbackResetOff(self):
        self.putVal('PitchFB_Reset', 0)        

    def WaitForFeedbackLocked(self,timeout=300):
        self.FeedbackOn()
        t0 = time.time()
        while self.getVal('PitchFB_Locked') != 1:
            epics.ca.poll()
            if time.time() - t0 > timeout:
                break
            time.sleep(0.1)
        print 'Feedback locked! '
        return  self.getVal('PitchFB_Locked')==1
        
    def CheckMonoPitch(self):
        tilt_val = self.getVal('Tilt_Fine')    
        if abs(tilt_val) < 2.0:
            print 'Mono tilt fine adjust looks OK'
        else:
            self.OptimizeMonoPitch()
        self.OptimizeMonoRoll()
        self.FeedbackOn()

    def OptimizeMonoPitch(self):
        print 'Need to Optimize Mono Pitch: '
        self.FeedbackOff()
        self.FeedbackResetOff()

        self.putVal('Tilt_Fine', 0)
        # 
        i0_setval  =  self.getVal('I0_Setpoint')

        i0max = -1.0
        fine_val = -1.0
        for i in range(80):
            fine_val = -4.0 + i * 0.1
            self.putVal('Tilt_Fine', fine_val)
            time.sleep(0.1)
            i0x = self.getVal('I0_Actual')
            if i0x > i0max:
                i0max = i0x
                fine_best = fine_val
            if i0max > 1.25*i0_setval:
                print 'no need for full search '
                self.putVal('Tilt_Fine', -3.5)
                time.sleep(0.1)
                self.putVal('Tilt_Fine', fine_best-0.5)
                self.FeedbackOn()
                return self.WaitForFeedbackLocked()
                
        # search with coarse tilt and presilt
        tilt_coarse0 = coarse_best =self.getVal('Tilt_Coarse')
        print 'Starting Coarse Val = ', tilt_coarse0
        self.putVal('Tilt_Fine', 0)        
        for step in (8e-4, 2.e-4):
            summax = 0
            for i in range(40):
                coarse_val = coarse_best - (i-20) * step
                self.putVal('Tilt_Coarse', coarse_val)
                time.sleep(0.1)
                sum = self.getVal('PreSlit_Sum')
                diff= self.getVal('PreSlit_Diff')
                i0x = self.getVal('I0_Actual')
                if sum > summax and (i0x > 0.1*i0_setval):
                    summax= sum
                    coarse_best = coarse_val
                    print 'see max Sum at ', coarse_best

            print 'step size %.5f -> coarse_best=%f' % (step,coarse_best)
        self.putVal('Tilt_Coarse', coarse_best)
        self.putVal('Tilt_Fine',  -1.5)
        self.FeedbackOn()
        return self.WaitForFeedbackLocked()        

    
if __name__ == '__main__':
    m = mono_control('13IDA:')
    
    time.sleep(0.1)
    x = m.WaitForShutterOpen()
    x = m.WaitForFeedbackLocked()
    print x
