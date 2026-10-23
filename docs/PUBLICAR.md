# Subir esta carpeta a GitHub por SSH

La carpeta ya tiene un commit inicial en `main` y el remoto `origin` configurado
como `git@github.com:canekzapata/rejilla.git`. Se comprobó por HTTPS que el remoto
no anunciaba ramas al preparar esta edición. No se ha hecho push.

En PowerShell:

```powershell
cd C:\Users\HP-PC\canek\herramientas\agent\rejilla-github
ssh -T git@github.com
git push -u origin main
```

SSH debe reconocer la cuenta de GitHub y su servidor. Si la conexión pide
configurar una clave o muestra `Permission denied (publickey)`, hay que completar
esa configuración antes del push. La comprobación automatizada por SSH de esta
sesión se detuvo porque Windows OpenSSH todavía no tenía registrada la clave
del servidor; no se cambió la confianza de SSH ni se crearon llaves.

Para cambios posteriores:

```powershell
git status
git add README.md partituras biblioteca-de-instrumentos research herramientas docs
git diff --cached --stat
git commit -m "describir el cambio"
git push
```

Los resultados de audio y video, los ZIPs, los entornos y los bancos opcionales
quedan fuera por `.gitignore`. Conserva el taller original como archivo local.
Si otra persona agregó cambios al remoto antes del primer push y Git lo rechaza,
revisa ese historial antes de integrarlo; no uses `--force` para reemplazarlo.

Guías oficiales:
- https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
