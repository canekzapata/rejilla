"""Interfaz de archivo y botones; no requiere escribir comandos una vez instalado Python."""
import os, subprocess, sys, threading, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog
BASE=Path(__file__).resolve().parent.parent
root=tk.Tk(); root.title('Rejilla - taller de música'); root.geometry('740x520')
archivo=tk.StringVar(value=str(BASE/'ejemplos/03-cancion.json')); motor=tk.StringVar(value='directo')
ttk.Label(root,text='Rejilla · producir música e imágenes',font=('Arial',18)).pack(pady=15)
ttk.Label(root,text='1. Elige una partitura.  2. Elige el motor.  3. Produce.').pack()
ttk.Entry(root,textvariable=archivo,width=94).pack(padx=12,pady=12)
def elegir():
    p=filedialog.askopenfilename(initialdir=BASE/'ejemplos',filetypes=[('Partitura JSON','*.json')])
    if p: archivo.set(p)
ttk.Button(root,text='Elegir partitura',command=elegir).pack()
ttk.Radiobutton(root,text='Directo: Python, sin FFmpeg (comparación didáctica)',variable=motor,value='directo').pack(pady=4)
ttk.Radiobutton(root,text='Rejilla: imagen espectral → FFmpeg → audio',variable=motor,value='rejilla').pack()
log=tk.Text(root,height=13,wrap='word'); log.pack(fill='both',expand=True,padx=12,pady=10)
def escribir(s): log.insert('end',s); log.see('end')
def iniciar():
    boton.configure(state='disabled'); seleccion=archivo.get(); modo=motor.get()
    def run():
        try:
            p=subprocess.Popen([sys.executable,str(BASE/'python/taller.py'),seleccion,'--motor',modo],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
            for line in p.stdout: root.after(0,escribir,line)
            p.wait(); root.after(0,escribir,'\nProceso terminado.\n' if p.returncode==0 else '\nRevisa el mensaje anterior y el manual.\n')
        except Exception as e: root.after(0,escribir,str(e)+'\n')
        finally: root.after(0,lambda:boton.configure(state='normal'))
    threading.Thread(target=run,daemon=True).start()
boton=ttk.Button(root,text='Producir audio + PNGs + GIF',command=iniciar); boton.pack(pady=8)
root.mainloop()
