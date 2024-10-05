# meta / cours

C'est un mémo à vocation interne (pour me souvenir de comment on fait les choses) mais qui sera peut-être utile à d'autres enseignants ou présentateurs.

## slides

### style reveal.js

A priori, c'est ce que j'utilise. Les slides sont plus naturelles qu'avec pandoc. La conversion en HTML n'est pas automatique mais il suffit de sauver la page du navigateur...

```sh
reveal-md test_slide_revealmd.md
```

### style pandoc

Pour convertir une slide markdown en HTML:
```sh
pandoc -t reavealjs -s test_slide_pandoc.md -o test_slide_pandoc.html
```
