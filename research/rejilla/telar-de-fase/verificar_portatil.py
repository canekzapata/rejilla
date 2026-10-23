from pathlib import Path
import subprocess
root=Path(__file__).resolve().parent
p=root/'telar-portatil-s20261021-48d35d4afd7e'/'telar-de-fase-s20261021-48d35d4afd7e.html'
t=p.read_text(encoding='utf-8')
s=t.split('<script type="module">')[1].split('</script>')[0]
assert 'import ' not in s and 'src="interfaz.mjs"' not in t
subprocess.run(['node','--input-type=module','--check'],input=s.encode('utf-8'),check=True)
print('HTML portátil: sintaxis válida, motor completo y sin importaciones externas.')
