# Notice d'utilisation
/!\/!\ Attention, pour pouvoir builder correctement ces images docker, il faut se placer à la racine du projet docker-files. Pourquoi ? car docker prend comme contexte de build le dossier courant et dans le dossier common, il y a un script commun aux deux images.

Dans le fichier common/common.py, changez l'url pour votre serveur GITLAB. (GITLAB_BASE_URL)
Dans le fichier cvs2git/cvs2git.py, changez les paramètres requis. (FIELDS TO SET)
Dans le fichier svn2git/svn2git.py, changez les paramètres requis. (FIELDS TO SET)

# Migrate CVS project to GIT

Build de l'image docker:
```
 docker build --no-cache -t cvs2git -f cvs2git/Dockerfile .
```

Run de l'image docker:
```
docker run
-e cvsuser=<TO_REPLACE>
-e cvspass=<TO_REPLACE>
-e group=<TO_REPLACE> 
-e project=<TO_REPLACE>
-e GITLAB_API_TOKEN=<TO_REPLACE>
-e gitlabuser=<TO_REPLACE>
-e gitlabpass=<TO_REPLACE>
cvs2git
```
On peut également passer tous ces paramètres dans un fichier d'environnement, par exemple ```project.cvs.env``` situé dans le dossier parent:
```
docker run --env-file=../project.cvs.env cvs2git
```

/!\/!\ Pour les projets CVS, les tags portant le même nom que les branches ne seront pas pris en compte.

# Migrate SVN project to GIT

Build de l'image docker:
```
 docker build --no-cache -t svn2git -f svn2git/Dockerfile .
```

Run de l'image docker:
```
docker run
-e svnuser=<TO_REPLACE>
-e svnpass=<TO_REPLACE>
-e svnroot=<TO_REPLACE>
-e trunkbase=<OPTIONAL>
-e branchesbase=<OPTIONAL>
-e tagsbase=<OPTIONAL>
-e group=<TO_REPLACE> 
-e project=<TO_REPLACE>
-e GITLAB_API_TOKEN=<TO_REPLACE>
-e gitlabuser=<TO_REPLACE>
-e gitlabpass=<TO_REPLACE>
-e nobranches=<OPTIONAL>
-e notags=<OPTIONAL>
-e processTagsAsBranches=<OPTIONAL>
-e gitlabproject=<OPTIONAL>
svn2git
```
*nobranches*: **False** par défaut. Si c'est *False*, cela migrera les branches. Si c'est *True*, cela ne les migrera pas.

*notags*: **False** par défaut. Si c'est *False*, cela migrera les tags. Si c'est *True*, cela ne les migrera pas.

*processTagsAsBranches*: **False** par défaut, parcours la branche develop et cherche les messages de commit "released version" pour recréer les tags (plus rapide car il y en a plusieurs centaines). 
**True**, checkout les tags comme les branches et permet de récupérer les tags peut importe leur nom (/!\ plus lent).

On peut également passer tous ces paramètres dans un fichier d'environnement, par exemple ```project.svn.env``` situé dans le dossier parent:

```
docker run --env-file=../project.svn.env svn2git
```

# Contournements pour SVN
Normalement sur de petit repo, la commande suivante permet de migrer le trunk, les branches et les tags:

```
git svn clone 
--trunk=/trunk/<PROJECT_NAME>
--branches=/branches/<PROJECT_NAME>
--tags=/tags/<PROJECT_NAME>
--authors-file=authors.txt 
<REPO_SVN>
<PROJECT_NAME>
```

Mais nous avons trop de branches et trop de tags pour pouvoir utiliser cette commande, du coup on migre le trunk dans un premier temps.

Puis on spécifie les branches:

```
git config --add svn-remote.svn.branches branches/<PROJECT_NAME>/*/<PROJECT_NAME>:refs/remotes/origin/*
```

Puis de déclencher le rappatriement avec la commande:
```
git svn fetch
```

Après quelques minutes ou dizaines de minutes d'attente, il suffit de checkout chacune des branches et d'exécuter à la fin cette commande pour pusher toutes les branches trouvées sur le repo distant:
```
git push -u --all
```



Pour les tags, il y en a tout simplement trop... Sachant que c'est déjà long avec les branches, c'est interminable pour les tags...

Le contournement est donc de se baser sur le message de commit qui est toujours de la même forme, par exemple:
```
"released version"
```

Du coup, on checkout chaque branche et dans chaque branche on récupère les commits contenant ce message et on créé un tag avec la version et le commit correspondant.

Simple et rapide, par contre ne prend pas en compte les tags SVN dont le nom ne suivrait pas cet exemple.

Autrement, si c'est important, il faut reporter les autres tags à la main (allez courage le plus gros est fait quand même!) ou trouver une autre solution?

Plus d'infos sur cet excellent article:
http://www.janosgyerik.com/practical-tips-for-using-git-with-large-subversion-repositories/



# Evolution possible pour les tags

Pour les plus téméraires et si les solutions précédentes ne vous conviennent pas, pour migrer les tags, on peut faire la même chose que pour les branches:
```
git config --add svn-remote.svn.tags tags/<PROJECT_NAME>/*/<PROJECT_NAME>:refs/remotes/origin/*
git svn fetch
```
Après **quelques dizaines de minutes d'attente voire plus**..., il suffit de checkout chacun des tags comme une branche et de recréer le tag:
```
git checkout $tag
git tag -a $tag $commit -m "SVN tag exported"

Exemple:
git tag -a <TAG_NAME> 9fceb02 -m "TAG_NAME"
```
On supprime ensuite la branche du tag, pour ne pousser que le tag à la fin
```
git checkout nextTag
# ou revenir sur la branche develop
git checkout develop

git branch -d $tag
```

A la fin, exécuter cette commande pour pusher tous les tags créés sur le repo distant:
```
git push -u --tags
```