# Streets of Brawl

Beat 'em up 2D estilo Streets of Rage (1991) hecho con **Godot 4.7** y **GDScript**.

## Controles
| Acción | Teclas |
|---|---|
| Mover | WASD / flechas |
| Golpear (3 seguidos = combo) | J / Z |
| Saltar | K / X |
| Reiniciar (game over / stage clear) | Enter |

## Estructura
- `scenes/` – `main.tscn` (nivel), `player.tscn`, `enemy.tscn`
- `scripts/fighter.gd` – lógica común (movimiento, salto, golpes, daño)
- `scripts/player.gd`, `scripts/enemy.gd` – control del jugador e IA
- `scripts/main.gd` – oleadas (`WAVES`), cámara y HUD
- `assets/` – sprites, sonidos y música (vacío por ahora)

Resolución interna 320x224 (como Mega Drive), ventana 960x672, escalado por viewport.
Todo el arte actual son rectángulos dibujados por código (placeholders).

## Git
- Rama `main`, `.gitignore` y `.gitattributes` ya configurados (se ignora `.godot/`).
- Conectar con GitHub: ver las instrucciones del chat o ejecutar
  `git remote add origin https://github.com/TU_USUARIO/TU_REPO.git && git push -u origin main`
