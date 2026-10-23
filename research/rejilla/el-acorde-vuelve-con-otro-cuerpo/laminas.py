import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from comun import *
def figura(title,sub='',n=1):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#e9ded1','axes.labelcolor':'#e9ded1','xtick.color':'#c7b6a5','ytick.color':'#c7b6a5','axes.edgecolor':'#77685e','axes.facecolor':'#171b21','figure.facecolor':'#171b21','savefig.facecolor':'#171b21'})
 f,a=plt.subplots(1,n,figsize=(12,6.3),squeeze=False);f.subplots_adjust(top=.79,bottom=.14,left=.11,right=.96,wspace=.28);f.text(.055,.93,title,fontsize=22);f.text(.055,.86,sub,color='#e9b46e');return f,a[0]
def salva(f,p):
 b=io.BytesIO();f.savefig(b,format='png',dpi=100);plt.close(f);guardar(p,b.getvalue())
