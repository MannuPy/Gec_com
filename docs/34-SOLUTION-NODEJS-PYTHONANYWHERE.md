# 34. Solution : Build du frontend React sans Node.js sur PythonAnywhere

> **Dernière mise à jour :** 1er juillet 2026 — mise à jour conformité code v2.

## Problème

PythonAnywhere ne fournit pas Node.js/npm dans son environnement Bash standard. Il est donc impossible d'exécuter `npm run build` directement sur PythonAnywhere pour compiler le frontend React/Vite.

**Ce document présente 3 solutions**, dans l'ordre recommandé :

| Solution | Difficulté | Quand l'utiliser |
|---|---|---|
| [A — nvm sur PythonAnywhere](#solution-a--nvm-sur-pythonanywhere-à-essayer-en-premier) | ⭐ Facile | Si ça fonctionne (plan Developer) |
| [B — Build local + SCP](#solution-b--build-en-local--upload-ssh-scp) | ⭐⭐ Moyen | Si nvm ne fonctionne pas |
| [C — GitHub Actions](#solution-c--github-actions-cicd-recommandée-long-terme) | ⭐⭐⭐ Avancé | Pour automatiser chaque déploiement |

---

## Solution A — nvm sur PythonAnywhere (à essayer en premier)

`nvm` est un gestionnaire de version Node.js qui s'installe dans votre dossier personnel — sans droits administrateur. Cela fonctionne sur PythonAnywhere Developer (internet sortant débloqué).

### A.1 Installer nvm

Dans la console **Bash PythonAnywhere** :

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

### A.2 Recharger le shell

```bash
source ~/.bashrc
```

Ou fermez la console et ouvrez-en une nouvelle.

### A.3 Vérifier que nvm est installé

```bash
nvm --version
# Doit afficher : 0.39.7 (ou similaire)
```

### A.4 Installer Node.js LTS

```bash
nvm install --lts
```

Durée : 1 à 2 minutes. Résultat attendu :
```
Downloading and installing node v20.x.x...
Now using node v20.x.x (npm v10.x.x)
```

### A.5 Vérifier Node.js et npm

```bash
node --version   # → v20.x.x
npm --version    # → 10.x.x
```

### A.6 Builder le frontend

```bash
cd ~/gescom-bf/frontend
npm install
npm run build
```

### A.7 Vérifier le build

```bash
ls ~/gescom-bf/frontend/dist/
# Doit afficher : index.html  assets/
```

**Si cette solution fonctionne → passez directement à l'étape 12 du guide principal.**

---

### ❌ Si nvm échoue (erreur réseau)

PythonAnywhere bloque parfois `raw.githubusercontent.com`. Essayez :

```bash
# Alternative 1 : wget
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Alternative 2 : installer depuis le miroir
curl -o nvm_install.sh https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh
bash nvm_install.sh
```

Si ça échoue toujours → passer à la **Solution B**.

---

## Solution B — Build en local + Upload SSH/SCP

Vous buildez le frontend sur **votre ordinateur** (où Node.js est installé) puis vous copiez les fichiers sur PythonAnywhere via SSH.

### Prérequis

- Node.js installé sur votre ordinateur ([nodejs.org](https://nodejs.org))
- Le plan Developer PythonAnywhere (SSH inclus)

### B.1 Vérifier Node.js sur votre ordinateur

Ouvrez un terminal sur **votre ordinateur** (pas PythonAnywhere) :

```bash
node --version
npm --version
```

Si pas installé → télécharger depuis [https://nodejs.org](https://nodejs.org) (version LTS).

### B.2 Cloner ou se placer dans le projet sur votre ordinateur

```bash
cd ~/votre-dossier/gescom-bf
# ou
git clone https://github.com/votre-nom/gescom-bf.git && cd gescom-bf
```

### B.3 Builder le frontend

```bash
cd frontend
npm install
npm run build
```

Résultat : un dossier `frontend/dist/` est créé avec les fichiers `index.html` et `assets/`.

### B.4 Utiliser le script de déploiement fourni

Le projet inclut un script tout-en-un (`scripts/deploy-frontend-ssh.sh`) :

```bash
cd ~/votre-dossier/gescom-bf
chmod +x scripts/deploy-frontend-ssh.sh

# Lancer le déploiement (remplacer mannu par votre username)
./scripts/deploy-frontend-ssh.sh mannu
```

Le script :
1. Build automatiquement le frontend
2. Vous demande votre mot de passe PythonAnywhere
3. Copie les fichiers via SCP
4. Recharge l'application si `PA_API_TOKEN` est défini

### B.5 Alternative — SCP manuel (sans le script)

Si vous préférez sans script :

```bash
# Sur votre ordinateur, dans le dossier gescom-bf/
cd frontend
npm install && npm run build

# Copier vers PythonAnywhere (vous demande le mot de passe PythonAnywhere)
scp -r dist/ mannu@ssh.pythonanywhere.com:/home/mannu/gescom-bf/frontend/
```

### B.6 Vérifier sur PythonAnywhere

Dans la console Bash PythonAnywhere :

```bash
ls ~/gescom-bf/frontend/dist/
# → index.html  assets/
```

### B.7 Recharger l'application

Dans l'onglet **Web** de PythonAnywhere → bouton **"Reload mannu.pythonanywhere.com"**.

---

## Solution C — GitHub Actions CI/CD (recommandée long terme)

Cette solution automatise **entièrement** le déploiement : chaque fois que vous poussez du code sur `main`, GitHub Actions build le frontend et met à jour PythonAnywhere automatiquement.

### C.1 Configurer les secrets GitHub

Dans votre dépôt GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** :

| Nom du secret | Valeur |
|---|---|
| `PA_USERNAME` | Votre username PythonAnywhere (ex. `mannu`) |
| `PA_SSH_PASSWORD` | Votre mot de passe PythonAnywhere (login) — utilisé par `sshpass` dans le workflow CI/CD |
| `PA_API_TOKEN` | Token API PythonAnywhere (voir §C.2) |

### C.2 Générer un token API PythonAnywhere

1. Connectez-vous sur PythonAnywhere
2. Menu **Account** (haut droite) → onglet **"API token"**
3. Cliquer **"Create a new API token"**
4. Copier la valeur et la coller dans le secret `PA_API_TOKEN`

### C.3 Le workflow est déjà prêt

Le fichier `.github/workflows/deploy-pythonanywhere.yml` est inclus dans le projet. Il se déclenche automatiquement à chaque push sur `main`.

### C.4 Tester le workflow manuellement

1. Allez sur GitHub → onglet **Actions**
2. Sélectionner le workflow **"Deploy to PythonAnywhere"**
3. Cliquer **"Run workflow"** → **"Run workflow"** (bouton vert)
4. Suivre l'exécution en temps réel

### C.5 Ce que fait le workflow automatiquement

```
push sur main
    ↓
GitHub Actions (Ubuntu)
    ↓
npm ci + npm run build     ← build le frontend
    ↓
scp dist/ → PythonAnywhere ← copie les fichiers
    ↓
git pull (backend)         ← met à jour le code backend
    ↓
flask db upgrade           ← applique les nouvelles migrations
    ↓
API PythonAnywhere reload  ← recharge l'application
    ↓
curl /health               ← vérifie que le site répond
```

---

## Tableau récapitulatif

| | Solution A (nvm) | Solution B (SCP local) | Solution C (GitHub Actions) |
|---|---|---|---|
| Node.js sur votre PC requis | Non | **Oui** | Non |
| Automatique après push | Non | Non | **Oui** |
| Configuration initiale | 5 min | 10 min | 20 min |
| Idéal pour | Test rapide | Usage quotidien | Production |

---

## Après avoir appliqué une solution

Quelle que soit la solution choisie, vérifier :

```bash
# Sur PythonAnywhere (console Bash)
ls ~/gescom-bf/frontend/dist/index.html
# → doit exister

# Dans le navigateur
# https://mannu.pythonanywhere.com/
# → page de connexion GesCom-BF
```

Si le site affiche encore une page blanche après avoir copié les fichiers : recharger l'application dans l'onglet **Web**.

---

## Références

- Guide de déploiement principal : `docs/33-GUIDE-COMPLET-MISE-EN-LIGNE-PYTHONANYWHERE.md`
- Script SCP : `scripts/deploy-frontend-ssh.sh`
- GitHub Actions : `.github/workflows/deploy-pythonanywhere.yml`
