#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from tkinter import *
import numpy as np
import matplotlib
# from scipy import *
from matplotlib import pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')

from scipy.integrate import odeint
import ipywidgets as wg
from IPython.display import display

from numpy import min, max
from scipy.signal import lti, step, impulse
import control.matlab as control

#plot features
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #, NavigationToolbar2TkAgg
from matplotlib.figure import Figure


"""initialize GUI"""
root=Tk()
root.title("PID GUI")
# root.geometry("1400x700")
# root.resizable(False, False)

"""Define classes"""
class Plant:
    def __init__(self,master):
#Create Title Box Frame        
        self.titlebox=Frame(master,borderwidth=5)
#Create Plant Frame
        self.fplant=Frame(master,borderwidth=5) 
#Create Gains Frame  
        self.fgain=Frame(master,borderwidth=5)
        #Create subFrame(s) [f is master, "k%_f" is slave 1-3, each slave has two entry_boxes on
        #  the far left, a decrease button, a slider, and an increase button]
        self.kp_f=Frame(self.fgain,borderwidth=5)
        self.ki_f=Frame(self.fgain,borderwidth=5)
        self.kd_f=Frame(self.fgain,borderwidth=5)
#Create empty list for later [Plant]
        self.lti_num=[] #for scipy input format, list of leading coeffs
        self.lti_denom=[-1111] #same as above, but set to trigger a special condition for first run
        self._Kp = None #trigger special condition on first run
        self._tauI = None #similar to above
        self._tauD = None #similar to above
#Create empty list for later [gains]
        self.PLLL=[] #Proportional Lower Limits List
        self.PULL=[] #Proportional Upper Limits List
        self.ILLL=[] #Integral Lower Limits List
        self.IULL=[] #Integral Upper Limits List
        self.DLLL=[] #Derivative Lower Limits List
        self.DULL=[] #Derivative Upper Limits List
        self.__kp=[] #List of confirmed Kp values
        self.__ki=[] #List of confirmed Ki values (now tauI)
        self.__kd=[] #List of coonfirmed Kd values (now taud)
#Create Widgets in Titlebox Frame
        self.maintitle=Label(self.titlebox,text='Interactive P.I.D. GUI',padx=450,pady=5,font=("Helvetica",24))
        self.maintitle.grid(sticky=EW)
#Create Widgets in Frame [plant] 
        #interact with lists        
        self.num=Entry(self.fplant,width=50,borderwidth=5,justify=CENTER)
        self.num.insert(0,"Enter leading coefficients one at a time")
        self.num_btn=Button(self.fplant,text="Pull Num Coeff.",command=self.pull_num)
        self.denom=Entry(self.fplant,width=50,borderwidth=5,justify=CENTER)
        self.denom.insert(0,"Enter leading coefficients one at a time")
        self.denom_btn=Button(self.fplant,text="Pull Denom Coeff.",command=self.pull_denom) 
        #clear the lists in case of error or new problem
        self.clear_num_btn=Button(self.fplant,text="Clear Numerator",command=self.clear_num)
        self.clear_denom_btn=Button(self.fplant,text="Clear Denominator",command=self.clear_denom)
        #labels for everything
        self.num_L=Label(self.fplant,text='Enter Numerator Coeff:',padx=1)
        self.num_LPad=Label(self.fplant,text='                                                       ',padx=1)
        self.denom_L=Label(self.fplant,text='                Enter Denominator Coeff:                \n (*Please enter this one first*):',padx=1)
        self.denom_LPad=Label(self.fplant,text='                                                                ',padx=1)
#Create Widgets in Frame/subframe [gains]
        self.PLL=Entry(self.kp_f,width=10,borderwidth=5,justify=LEFT)
        self.PLL.insert(0,0)
        self.PUL=Entry(self.kp_f,width=10,borderwidth=5,justify=LEFT)
        self.PUL.insert(0,10)
        self.PLLB=Button(self.kp_f,text="update P Lower Limits",command=self.update_PLL)
        self.PULB=Button(self.kp_f,text="Update P Upper Limits",command=self.update_PUL)
        #adjustable limits
        self.kp=Scale(self.kp_f,from_=0,to=10,orient=HORIZONTAL,resolution=.05)
        self.PIb=Button(self.kp_f,text='+',padx=4,pady=5,command=self.p_up)
        self.PDb=Button(self.kp_f,text='-',padx=5,pady=5,command=self.p_down)
        self.confirm_btnP=Button(self.kp_f,text='Confirm Kp value',command=self.confirmP)
        self.kp_L=Label(self.kp_f,text='Proportional:',padx=15)
        self.PL_L=Label(self.kp_f,text='                           Limits:',padx=5)
        #sliders with button action, .1 sensitivity, button to update
        self.ILL=Entry(self.ki_f,width=10,borderwidth=5,justify=LEFT)
        self.ILL.insert(0,0)
        self.IUL=Entry(self.ki_f,width=10,borderwidth=5,justify=LEFT)
        self.IUL.insert(0,10)
        self.ILLB=Button(self.ki_f,text="update I Lower Limits",command=self.update_ILL)
        self.IULB=Button(self.ki_f,text="Update I Upper Limits",command=self.update_IUL)
        #adjustable limits
        self.ki=Scale(self.ki_f,from_=0,to=10,orient=HORIZONTAL,resolution=.05)
        self.IIb=Button(self.ki_f,text='+',padx=4,pady=5,command=self.i_up)
        self.IDb=Button(self.ki_f,text='-',padx=5,pady=5,command=self.i_down)
        self.confirm_btnI=Button(self.ki_f,text='Confirm tauI value',command=self.confirmI)
        #sliders with button action, .1 sensitivity
        self.ki_L=Label(self.ki_f,text='    Integral:',padx=15)
        self.IL_L=Label(self.ki_f,text='                            Limits:',padx=5)
        #labels
        self.DLL=Entry(self.kd_f,width=10,borderwidth=5,justify=LEFT)
        self.DLL.insert(0,0)
        self.DUL=Entry(self.kd_f,width=10,borderwidth=5,justify=LEFT)
        self.DUL.insert(0,10)
        self.DLLB=Button(self.kd_f,text="update D Lower Limits",command=self.update_DLL)
        self.DULB=Button(self.kd_f,text="Update D Upper Limits",command=self.update_DUL)
        #adjustable limits
        self.kd=Scale(self.kd_f,from_=0,to=10,orient=HORIZONTAL,resolution=.05)
        self.DIb=Button(self.kd_f,text='+',padx=4,pady=5,command=self.d_up,)
        self.DDb=Button(self.kd_f,text='-',padx=5,pady=5,command=self.d_down)
        self.confirm_btnD=Button(self.kd_f,text='Confirm tauD value',command=self.confirmD)
        #same as above
        self.kd_L=Label(self.kd_f,text=' Derivative:',padx=15)
        self.DL_L=Label(self.kd_f,text='                            Limits:',padx=5)  
        #labels
#Place Widgets in Frame [plant]
        self.maintitle.grid(row=1,column=2,rowspan=4)
        self.num_L.grid(row=2,column=0,rowspan=1)
        self.num_LPad.grid(row=2,column=2,rowspan=1)
        self.num.grid(row=2,column=1)
        self.num_btn.grid(row=3,column=1)
        self.clear_num_btn.grid(row=4,column=1)
        self.denom_L.grid(row=5,column=0,rowspan=1)
        self.denom_LPad.grid(row=5,column=2,rowspan=1)
        self.denom.grid(row=5,column=1)
        self.denom_btn.grid(row=6,column=1)
        self.clear_denom_btn.grid(row=7,column=1)
#Place Widgets in subFrame(s) [gains]
        self.kp_L.grid(row=0,column=0,rowspan=3)
        self.PL_L.grid(row=0,column=1,columnspan=2)
        self.PLL.grid(row=1,column=1)
        self.PLLB.grid(row=1,column=2)
        self.PUL.grid(row=2,column=1)
        self.PULB.grid(row=2,column=2)
        self.PDb.grid(row=1,column=3)
        self.kp.grid(row=1,column=4)
        self.PIb.grid(row=1,column=5)
        self.confirm_btnP.grid(row=0,column=6,rowspan=3)

        self.ki_L.grid(row=0,column=0,rowspan=3)
        self.IL_L.grid(row=0,column=1,columnspan=2)
        self.ILL.grid(row=1,column=1)
        self.ILLB.grid(row=1,column=2)
        self.IUL.grid(row=2,column=1)
        self.IULB.grid(row=2,column=2)
        self.IDb.grid(row=1,column=3)
        self.ki.grid(row=1,column=4)
        self.IIb.grid(row=1,column=5)
        self.confirm_btnI.grid(row=0,column=6,rowspan=3)

        self.kd_L.grid(row=0,column=0,rowspan=3)
        self.DL_L.grid(row=0,column=1,columnspan=2)
        self.DLL.grid(row=1,column=1)
        self.DLLB.grid(row=1,column=2)
        self.DUL.grid(row=2,column=1)
        self.DULB.grid(row=2,column=2)
        self.DDb.grid(row=1,column=3)
        self.kd.grid(row=1,column=4)
        self.DIb.grid(row=1,column=5)
        self.confirm_btnD.grid(row=0,column=6,rowspan=3)

#Place the Frame in Window [titlebox]
        self.titlebox.pack()
    
#Place the Frame in Window [plant]
        self.fplant.pack()
    
#Place subFrames in Frame [gains]

        self.kp_f.pack()
        self.ki_f.pack()
        self.kd_f.pack()
#Place Frame in Window [gains]

        self.fgain.pack()
#PID tuner dummy plot
        self.p = Figure(figsize=(10,5), dpi=100)
        self.a = self.p.add_subplot(111)
        self.a.set_xlabel('Time (sec)')
        self.a.set_ylabel('Amplitude')
        self.a.set_title('Step Response P.I.D. Plot')
        self.canvas = FigureCanvasTkAgg(self.p, master = root)
        self.canvas.get_tk_widget().pack()        
#Class Methods
    #PLANT
    def pull_num(self):
        self.var1=self.num.get()
        self.lti_num.append(float(self.var1))
        print(self.lti_num)
        self.plot()
    def pull_denom(self):
        if (self.lti_denom[0]==(-1111)):
            self.lti_denom=[]
        self.var1=self.denom.get()
        self.lti_denom.append(float(self.var1))
        print(self.lti_denom)
        self.plot()
    def clear_num(self): #clears the transfer function numerator for re-entry
        self.lti_num.clear()
        self.lti_num = []
        print("cleared")
    def clear_denom(self):
        self.lti_denom.clear() #clears the transfer function denominator for re-entry
        self.lti_denom = [-1111]
        print("cleared")
# --------------------------------------------------------------------------------------------------------------------
    def plot(self):
        #self._Kp.append(-1)
        #self._tauI.append(-1)
        #self._tauD.append(-1)
        if self._Kp==None: #make default plot with no errors and that will take inputs
            self._Kp=[0]
        if self._tauI==None: #make default plot with no errors and that will take inputs
            self._tauI=[1]
        if self._tauD==None: #make default plot with no errors and that will take inputs
            self._tauD=[0]
        tf = control.tf(self.lti_num,self.lti_denom)
        Gc = self._Kp[-1]*control.tf(((self._tauD[-1]*            self._tauI[-1]),self._tauI[-1],1),(self._tauI[-1],0))

        Hs = (tf*Gc)/(1+(tf*Gc))
        print(Hs)
        T = np.linspace(0,25,1000)
        self.a.clear()
        # recalculate t and s to get smooth plot
        y,t = control.step(Hs, T)
        u,t = control.step(tf, T)
        self.a.plot(t, u,'b-',linewidth=2,label='Y(s) Original')
        self.a.plot(t, y,'r-',linewidth=2,label='Y(s) Using PID')
        self.a.set_xlabel('Time (sec)')
        self.a.set_ylabel('Amplitude')
        self.a.set_ylim(min(u),(max(u)+1))
        self.a.set_title('Step Response P.I.D. Plot')
        self.a.legend(loc='best')
#         self.a.legend((y), ('Tuned Controller Output'), 'upper right')
        
        self.canvas.draw()
        self.a.clear()
#         self.canvas.itemconfig(self.a)
        """need to add a button for command"""
        return self.lti_denom, self.lti_num 
#---------------------------------------------------------------------------------------------------------------------
    #GAINS
    def update_PLL(self):
        self.PLLL.append(int(self.PLL.get()))
        self.kp.configure(from_=self.PLLL[-1])
    def update_PUL(self):
        self.PULL.append(int(self.PUL.get()))
        self.kp.configure(to=self.PULL[-1])

    def update_ILL(self):
        self.ILLL.append(int(self.ILL.get()))
        self.ki.configure(from_=self.ILLL[-1])
    def update_IUL(self):
        self.IULL.append(int(self.IUL.get()))
        self.ki.configure(to=self.IULL[-1])

    def update_DLL(self):
        self.DLLL.append(int(self.DLL.get()))
        self.kd.configure(from_=self.DLLL[-1])
    def update_DUL(self):
        self.DULL.append(int(self.DUL.get()))
        self.kd.configure(to=self.DULL[-1])


    #increase/decrease buttons
    def p_up(self):
        self.var1=self.kp.get()
        self.var1=self.var1+.05
        self.kp.set(self.var1)
    def p_down(self):
        self.var1=self.kp.get()
        self.var1=self.var1-.05
        self.kp.set(self.var1)

    def i_up(self):
        self.var1=self.ki.get()
        self.var1=self.var1+.05
        self.ki.set(self.var1)
    def i_down(self):
        self.var1=self.ki.get()
        self.var1=self.var1-.05
        self.ki.set(self.var1)

    def d_up(self):
        self.var1=self.kd.get()
        self.var1=self.var1+.05
        self.kd.set(self.var1)
    def d_down(self):
        self.var1=self.kd.get()
        self.var1=self.var1-.05
        self.kd.set(self.var1)
    
    #Pull out kp,taui,taud ; replot
    def confirmP(self):
        self.var1=self.kp.get()
        self.__kp.append(float(self.var1))
        print(self.__kp[-1])
        self._Kp.append(self.__kp[-1])
        self.plot()

    def confirmI(self):
        self.var1=self.ki.get()
        self.__ki.append(float(self.var1))
        print(self.__ki[-1])
        self._tauI.append(self.__ki[-1])
        self.plot()

    def confirmD(self):
        self.var1=self.kd.get()
        self.__kd.append(float(self.var1))
        print(self.__kd[-1])
        self._tauD.append(self.__kd[-1])
        self.plot()
        print(self._tauD)
   

   
"""Main Program"""
z = Plant(root)
root.mainloop()

