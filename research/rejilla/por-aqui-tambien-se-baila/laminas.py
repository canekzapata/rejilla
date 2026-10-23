import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from comun import *
def figura(title,sub='',n=1):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#253438','axes.labelcolor':'#253438','axes.edgecolor':'#90918b','axes.facecolor':'#f5f1e5','figure.facecolor':'#f5f1e5','savefig.facecolor':'#f5f1e5'})
 f,a=plt.subplots(1,n,figsize=(12,6.3),squeeze=False);f.subplots_adjust(top=.78,bottom=.14,left=.08,right=.96,wspace=.28);f.text(.055,.93,title,fontsize=22);f.text(.055,.86,sub,color='#627370');return f,a[0]
def png(f):
 b=io.BytesIO();f.savefig(b,format='png',dpi=100);plt.close(f);return b.getvalue()
def salva(f,p):guardar(p,png(f))
