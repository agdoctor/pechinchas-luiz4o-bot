---
description: Sincronizar código e Reiniciar o Bot (Modo Turbo)
---

// turbo-all
Este workflow automatiza o processo de salvar as alterações e preparar o bot na Square Cloud.

1. Salvar alterações pendentes no Git
```powershell
git add .
git commit -m "chore: manual sync from mobile"
git push
```

2. Instrução final
Acesse o painel da Square Cloud e clique em 'Restart' para aplicar as mudanças.
