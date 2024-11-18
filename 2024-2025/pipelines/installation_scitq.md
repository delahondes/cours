# A propos de ce document

Ce document reprend en détail les instructions déjà présentes dans scitq.readthedocs.io, et détaille tout ce qui doit être fait sur l'instance et dans OVH.


## installation scitq

- aller sur https://www.ovh.com, puis public cloud et cliquer sur l'offre 200 €, créer le compte
- une fois le projet créer, il faut l'activer, descendre dans Project Management -> Contacts and rights -> Enable  : il faut entrer une CB qui n'est pas prélevée.
- Eventuellement Project Management -> Quotas and Regions : jeter un oeil sur les quotas et activer une région voisine de la région principale
- Ajouter la clé SSH : Project Management -> SSH Keys
- Créer un compte Horizon: Project Management -> Users and roles -> New user: administrator (premier choix)
- Créer une instance: Compute -> Instance -> Create instance D2-4 : Ubuntu 24.04 : Graveline 9 : Clé SSH créée ci dessus : Réseau public seulement : facturation heure
- Optionnellement: activer un Dynamique DNS comme afraid.org
- Se connecter en ssh: `ssh ubuntu@<IP address>`, installer mosh: `sudo apt install mosh`
- Se deconnecter puis se reconnecter en mosh: `mosh ubuntu@<IP address>`

```sh
ufw allow ssh
ufw allow 60000:61000/udp
ufw allow from <mon-adresse-IP>
ufw enable
ufw status
```

 - Installer scitq, si pas rc: `pip install --break-system-packages scitq`:
	 - On est en rc, donc il faut obtenir le code,
		 - soit: `git clone https://github.com/gmtsciencedev/scitq.git` puis `git checkout develop` (cette dernière commande nous met sur la branche `develop`)
		 - soit rsync depuis sa machine (recommander pour modifier scitq): `rsync -av --exclude .git --exclude env --exclude build --delete scitq ubuntu@<address IP instance>:` 
	- Ensuite on se rend dans le dossier du code (a priori `/home/ubuntu/scitq`) et en tant que root on `apt install -y python3-pip postgresql; pip install --break-system-packages .`
	- On déploie:
```sh
sudo -u postgres createuser -d root
createdb scitq
scitq-manage db init

cp templates/production/scitq.conf /etc/
vi /etc/scitq.conf
# il faut changer à minima SCITQ_SERVER avec un nom public du serveur ou l'IP publique du serveur
# la ligne PYTHONPATH peut être supprimée

cp templates/production/scitq-*.service /etc/systemd/system/
cp templates/production/scitq.target /etc/systemd/system/
pip install --break-system-packages pyuwsgi
systemctl daemon-reload
mkdir /var/log/scitq
systemctl enable scitq-main scitq-queue scitq.target



```

Suivre https://scitq.readthedocs.io/en/latest/install/#ansible
avec deux exceptions:
- A cause d'Ubuntu 24.04, il faut utiliser python 3.10 (cassé à partir de 3.11) pour créer le venv, après tout est bon:

```bash
add-apt-repository ppa:deadsnakes/ppa -y
apt install python3.10 python3.10-venv python3.10-dev
python3.10 -m venv /root/ansibleenv
```

 - sauf que la version minimale de `/etc/ansible/inventory/02-scitq` est suffisante avec scitq_src là où est le source,  s3 and co utilise rclone maintenant dans la v1.3, les autres variables sont donc obsolètes:
```ini
[scitq:vars]
keyname=scitq
scitq_src=/home/ubuntu/scitq
```

Utiliser Horizon (compte précédemment créé) via https://horizon.cloud.ovh.net:
- déployer la clef publique créée ci-dessus en l'appelant scitq dans toutes les régions que vous comptez utiliser

Créer un object storage type S3 1-AZ region (à Graveline par exemple), linker à l'utilisateur Horizon principal, puis regardez les user à la fin demandez l'export rclone.
Malheureusement le fichier doit être modifié:
- Renommer juste la source de `[BackupStorageS3]` en `[s3]`
- Sur l'utilisateur dans le manager, demandez à voir la clé secrète, et ajoutez la dans le fichier avec `secret_access_key=...` et enlevez la ligne `env_auth = true`

Copiez le fichier ainsi modifié dans `/root/.config/rclone.conf` et dans `/etc/rclone.conf`. 

Enfin, dans le manager OVH, Project Management, User and roles, exporter l'Openstack RC file. Mettre toutes les variables du fichier dans `/etc/scitq.conf` 
NB le mot de passe ne doit pas être mis avec un input mais avec sa valeur en clair, obtenue au moment de la création du compte Horizon, puis comme c'est indiqué dans https://scitq.readthedocs.io/en/latest/specific/#ovh  et plus précisément dans https://scitq.readthedocs.io/en/latest/specific/#ovh-availability, il faut ajouter les items sur la disponibilité du genre et la région préférée, via les chiffres indiqués par OVH dans le manager Project Management, Quotas and Regions, colonne vCPU:

```sh
OVH_REGIONS="GRA11 GRA9 DE1 RBX-A SBG5 UK1 WAW1 BHS5"
OVH_CPUQUOTAS="34 4 6 6 6 6 6 6"
PREFERRED_REGIONS="ovh:GRA11"
```
NB: ne mettez que les régions qui ont reçu la clé SSH
NB2: tenez compte du serveur scitq lui même dans les quotas (c'est à dire vous devez déduire le quota utilisé du quota total sur la page OVH)
![[Pasted image 20241117103919.png]]
NB3 mettez la plus grosse région dispo en région préférée.
NB4 ne prenez pas les régions "locales" comme Marseille, Amsterdam ou Bruxelles, les noms d'image sont différents (et Ubuntu 20.04 n'existe pas sous son nom standard)

Puis allez sur : https://api.ovh.com/createToken/index.cgi?GET=/*
Créer une clé à durée indéterminée.

Renseigner les variables suivantes dans /etc/scitq.conf:
```
OVH_APPLICATIONKEY=<application key>
OVH_APPLICATIONSECRET=<application secret>
OVH_CONSUMERKEY=<consumer key>
```

Tester `scitq-ovh-updater` en le lançant à la main en tant que root.

Tout à la fin, ajouter la tâche cron, c.a.d. créer le fichier `/etc/cron.d/scitq`
```cron
# scitq cron
PATH=/usr/local/bin

# update ovh
46 * * * * root scitq-ovh-updater >> /var/log/scitq/cron.log 2>&1
```

et redémarrer cron: `systemctl restart cron`

## Copie des ressources

Sur bioit j'ai ajouté la ressource rclone ainsi créée comme s3jussieu

```sh
rclone copy s3:rnd/resource/chm13v2.0.tgz s3jussieu://scitq/resource/ --progress
rclone copy azure:rnd/resource/metaphlan4.1/metaphlan4.1.tgz s3jussieu://scitq/resource/ --progress
```


## Limites liées au systèmes de test

Dans ce système de test, les quotas sont tout petits et il faut souvent ajuster à la main (ou il faudrait aussi introduire au moins des quotas mémoire dans scitq)