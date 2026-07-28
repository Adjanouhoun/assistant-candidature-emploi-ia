# Déploiement OVH — Assistant candidature emploi IA

## Périmètre de la première mise en ligne

Le POC sera exposé publiquement en HTTPS derrière le Nginx déjà présent sur la
VM. PostgreSQL et Airflow ne sont pas publics. Les CV sont utilisés
temporairement, ne sont pas persistés et l'envoi à Gemini reste soumis au
consentement explicite de l'utilisateur. Le quota Gemini doit être surveillé.

## Préconditions à confirmer

1. Un sous-domaine dédié, par exemple `emploi.votre-domaine.fr`, pointe par DNS
   vers l'IPv4 de la VM OVH.
2. Les ports TCP 80 et 443 sont ouverts dans le pare-feu OVH et sur la VM.
3. Docker Engine avec le plugin Compose et le Nginx déjà utilisé par
   `data-pipeline-mobility` sont disponibles.
4. La VM dispose des secrets de production dans un fichier `.env` non versionné.
5. L'usage mémoire est contrôlé, car cette VM héberge déjà
   `data-pipeline-mobility`. Si les services Airflow et la synchronisation
   nationale compromettent la stabilité, l'upgrade 8 cœurs / 16 Go est requis
   avant l'activation nationale.

## Variables de production

Créer `.env` à partir de `.env.example`, puis définir au minimum :

```text
POSTGRES_PASSWORD=<secret-long-et-unique>
AIRFLOW_ADMIN_PASSWORD=<secret-long-et-unique>
AIRFLOW_JWT_SECRET=<secret-long-et-unique>
FRANCE_TRAVAIL_CLIENT_ID=<identifiant-production>
FRANCE_TRAVAIL_CLIENT_SECRET=<secret-production>
LBA_API_KEY=<clé-si-utilisée>
GEMINI_API_KEY=<clé-si-utilisée>
GEMINI_MODEL=gemini-3.5-flash-lite
SYNC_REGION_CODES=
NATIONAL_SYNC_START_DATE=2000-01-01
STREAMLIT_HOST_PORT=8502
AIRFLOW_PARALLELISM=2
AIRFLOW_MAX_ACTIVE_TASKS_PER_DAG=1
```

Ne pas inscrire de valeur réelle dans le dépôt.

## Procédure contrôlée

1. Cloner le dépôt sur la VM et se placer sur la branche de livraison validée.
2. Créer le fichier `.env` avec les valeurs de production.
3. Vérifier la configuration sans l'afficher :

   ```bash
   docker compose --env-file .env config --quiet
   ```

4. Initialiser les bases et services :

   ```bash
   docker compose --env-file .env up -d --build
   ```

5. Copier `deploy/nginx/assistant-candidature-emploi.conf` vers
   `/etc/nginx/sites-available/`, créer le lien dans `sites-enabled/`, puis
   vérifier et recharger Nginx.
6. Générer le certificat HTTPS avec Certbot pour
   `emploi.amadouadjanouhoun.fr` après propagation du DNS.
7. Vérifier l'état des conteneurs et les journaux sans afficher de secrets.
8. Ouvrir le domaine HTTPS, s'authentifier, vérifier la recherche, le profil et
   le parcours de candidature sans transmettre de candidature réelle.
9. Déclencher un premier cycle Airflow contrôlé, vérifier le volume d'offres et
   l'usage CPU/RAM/disque avant de laisser le cycle national tourner. Les limites
   par défaut (`2` tâches globales et `1` tâche par DAG) sont volontaires sur le
   VPS partagé ; ne pas les relever sans une nouvelle mesure de capacité.

## Retour arrière

En cas de problème applicatif, arrêter uniquement cette pile :

```bash
docker compose --env-file .env down
```

Cette commande préserve les volumes PostgreSQL. Elle ne touche pas au
projet `data-pipeline-mobility` présent sur la même VM.
