"""Capturas de estados calculados mientras se construye la pieza."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from comun import guardar
BG='#07151e';FG='#dcebef';C=['#7de9de','#b8b0f4','#eac984','#fa8d9d']
def figura(titulo,sub='',n=1):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':FG,'axes.labelcolor':FG,'xtick.color':FG,'ytick.color':FG,'axes.edgecolor':'#36525d','axes.facecolor':BG,'figure.facecolor':BG,'savefig.facecolor':BG})
 fig,ax=plt.subplots(1,n,figsize=(12,6.3),squeeze=False);fig.subplots_adjust(top=.81,bottom=.14,left=.08,right=.96,wspace=.27)
 fig.text(.06,.93,titulo,fontsize=22,color=FG);fig.text(.06,.87,sub,fontsize=10,color=C[0]);return fig,ax[0]
def salva(fig,p):
 import io
 b=io.BytesIO();fig.savefig(b,format='png',dpi=100);plt.close(fig);guardar(p,b.getvalue())
def red_lamina(red,p):
 fig,axs=figura('El lago empieza en una red','32 placas · aristas compartidas de Traspuesta 227 · modelo acústico a escala 1:32',2)
 for a in red['aristas']:
  v=np.array(a['puntos']);axs[0].plot(v[:,0],1-v[:,1],color=C[0],lw=1)
 pp=red['placas'];axs[0].scatter([q['centro'][0] for q in pp],[1-q['centro'][1] for q in pp],c=[q['f0'] for q in pp],cmap='winter',s=25);axs[0].set_aspect('equal');axs[0].set_title('Región conectada y vecindad',color=FG)
 for i,s in enumerate(red['estados']):axs[1].plot(s['frecuencias'],label=f'invierno {i+1}',alpha=.75)
 axs[1].set_title('Los acoplamientos conservan memoria',color=FG);axs[1].set_xlabel('modo de la red');axs[1].set_ylabel('Hz');axs[1].legend(facecolor=BG,labelcolor=FG);salva(fig,p)
