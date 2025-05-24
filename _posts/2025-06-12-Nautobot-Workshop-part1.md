---
title: Nautobot Workshop Blog Series - Part 1 Environment Setup
date: 2025-06-12 9:00:00 -6
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 1: Setting Up the Nautobot Workshop Lab Environment

### System Requirements
Ubuntu 24.04 (VM, or bare metal)

- 4 vCPUs and 8 GB RAM (minimum)
- Internet access
- GitHub account

1. Once you have your VM or bare metal Ubuntu machine built get containerlab up and running. Use their [installation](https://containerlab.dev/install/) page and follow the instructions.
2. Next head over [here](https://containerlab.dev/manual/vrnetlab/#vrnetlab) and get vrnetlab installed as well.
3. Get the CEOS and IOL images copied to your containerlab instance, you will need to provide these yourself. Copy your IOL 17.12.01 file to the ```~/vrnetlab/cisco/iol folder```, your folder should look something like this:

   ```bash
   ubuntu@containerlabs:~/vrnetlab/cisco/iol$ tree
   .
   ├── cisco_iol-17.12.01.bin
   ├── docker
   │   ├── Dockerfile
   │   └── entrypoint.sh
   ├── Makefile
   └── README.md

   2 directories, 5 files
   ```

4. Make sure the x86_64_crb_linux-adventerprisek9-ms file has been renamed to cisco_iol-17.12.01.bin. To convert the IOL bin to a docker container run the following:
   
   ```bash
   ubuntu@containerlabs:~/vrnetlab/cisco/iol$ make docker-image
   for IMAGE in cisco_iol-17.12.01.bin; do \
           echo "Making $IMAGE"; \
           make IMAGE=$IMAGE docker-build; \
           make IMAGE=$IMAGE docker-clean-build; \
   done
   Making cisco_iol-17.12.01.bin
   make[1]: Entering directory '/home/ubuntu/vrnetlab/cisco/iol'
   --> Cleaning docker build context
   rm -f docker/*.qcow2* docker/*.tgz* docker/*.vmdk* docker/*.iso docker/*.xml docker/*.bin
   rm -f docker/healthcheck.py docker/vrnetlab.py
   Building docker image using cisco_iol-17.12.01.bin as vrnetlab/cisco_iol:17.12.01
   echo "ok"
   ok
   ....
   => [9/9] RUN chmod +x /iol/iol.bin                                                                                                  0.8s
    => exporting to image                                                                                                               5.0s
    => => exporting layers                                                                                                              4.9s
    => => writing image sha256:7a37f24259f42f320c6059423ed51db2e794739e873ac99a8d665b71df740a56                                         0.0s
    => => naming to docker.io/vrnetlab/cisco_iol:17.12.01                                                                               0.0s
   make[1]: Leaving directory '/home/ubuntu/vrnetlab/cisco/iol'
   make[1]: Entering directory '/home/ubuntu/vrnetlab/cisco/iol'
   --> Cleaning docker build context
   rm -f docker/*.qcow2* docker/*.tgz* docker/*.vmdk* docker/*.iso docker/*.xml docker/*.bin
   rm -f docker/healthcheck.py docker/vrnetlab.py
   make[1]: Leaving directory '/home/ubuntu/vrnetlab/cisco/iol'
   ```

5. Copy the CEOS image from the Arista website to your home folder and convert it to a docker image as well. When finished you should have two docker images, one for each router image.
   
   ```bash
   ubuntu@containerlabs:~$  docker import cEOS64-lab-4.34.0F.tar ceos:4.34.0F
   sha256:1e22e6e288322fa4ddf98d31efaed2c9a9be14112eea015f1d0a6d6f72601b04
   ubuntu@containerlabs:~$ docker images
   REPOSITORY                         TAG        IMAGE ID       CREATED          SIZE
   ceos                               4.34.0F    1e22e6e28832   11 seconds ago   2.49GB
   vrnetlab/cisco_iol                 17.12.01   7a37f24259f4   5 minutes ago    704MB
   ```

6. Clone the workshop [repository](https://github.com/byrn-baker/Nautobot-Workshop.git).
7. Install Poetry.
   
   ```bash
   $ curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.6.1 python3 -
   $ export PATH="$HOME/.local/bin:$PATH"
   ```

8. Using a new terminal window and from the nautobot-docker-compose folder setup the poetry environment. Following these steps should get your nautobot container built and you should see a similar output and 3 images.
   
   ```bash
   ubuntu@containerlabs:~/Nautobot-Workshop/nautobot-docker-compose$ pip3 install invoke toml
   ubuntu@containerlabs:~/Nautobot-Workshop/nautobot-docker-compose$ poetry shell
   (nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/Nautobot-Workshop/nautobot-docker-compose$ poetry lock
   (nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/Nautobot-Workshop/nautobot-docker-compose$ invoke build
   #20 [nautobot nautobot 5/5] RUN pyuwsgi --cflags | sed 's/ /\n/g' | grep -e "^-DUWSGI_SSL$"
   #20 0.330 -DUWSGI_SSL
   #20 DONE 0.3s

   #21 [nautobot] exporting to image
   #21 exporting layers
   #21 exporting layers 20.6s done
   #21 writing image sha256:d889e3763dfe9397c740c7c7aeeaefee984c61d98f14183ba5b2b75bcaeecc52 done
   #21 naming to docker.io/yourrepo/nautobot-docker-compose:local done
   #21 DONE 20.7s

   #22 [nautobot] resolving provenance for metadata file
   #22 DONE 0.0s
    nautobot  Built
    (nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ docker images
   REPOSITORY                         TAG        IMAGE ID       CREATED          SIZE
   ceos                               4.34.0F    1e22e6e28832   3 minutes ago    2.49GB
   vrnetlab/cisco_iol                 17.12.01   7a37f24259f4   8 minutes ago    704MB
   yourrepo/nautobot-docker-compose   local      d889e3763dfe   14 minutes ago   1.43GB
   ```

9. In the ```nautobot-docker-compose``` folder make sure you have your ```environments/local.env``` & ```environments/creds.env``` exists and your passwords are set how you want them.
10. Update the [pyproject.toml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/nautobot-docker-compose/pyproject.toml) to include the Nautobot APPs we will be using in our workshop.

```bash
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ poetry lock
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ poetry install
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ invoke build
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ invoke debug
/home/ubuntu/nautobot-docker-compose/tasks.py:263: SyntaxWarning: invalid escape sequence '\$'
  export_cmd = 'exec db sh -c "mysqldump -u \${NAUTOBOT_DB_USER} –p \${NAUTOBOT_DB_PASSWORD} \${NAUTOBOT_DB_NAME} nautobot > /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:266: SyntaxWarning: invalid escape sequence '\$'
  export_cmd = 'exec db sh -c "pg_dump -h localhost -d \${NAUTOBOT_DB_NAME} -U \${NAUTOBOT_DB_USER} > /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:285: SyntaxWarning: invalid escape sequence '\$'
  import_cmd = 'exec db sh -c "mysql -u \${NAUTOBOT_DB_USER} –p \${NAUTOBOT_DB_PASSWORD} < /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:288: SyntaxWarning: invalid escape sequence '\$'
  import_cmd = 'exec db sh -c "psql -h localhost -U \${NAUTOBOT_DB_USER} < /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
Starting Nautobot in debug mode...
Running docker compose command "up"
 db Pulling 
 redis Pulling 
 f18232174bc9 Pulling fs layer 
 b555fdaa5ef5 Pulling fs layer 
 c96d76ec6d7d Pulling fs layer 
 66d15cf00aa7 Pulling fs layer 
 834f5dbdfbb2 Pulling fs layer 
 5883dc8e1ee8 Pulling fs layer 
 4f4fb700ef54 Pulling fs layer 
 439ece23a1c1 Pulling fs layer 
 4f4fb700ef54 Waiting 
 834f5dbdfbb2 Waiting 
 66d15cf00aa7 Waiting 
 5883dc8e1ee8 Waiting 
 b555fdaa5ef5 Downloading [=====================================>             ]     720B/951B
 ....
 celery_worker-1  | --- ***** ----- 
celery_worker-1  | -- ******* ---- Linux-6.8.0-59-generic-x86_64-with-glibc2.36 2025-05-10 02:37:57
celery_worker-1  | - *** --- * --- 
celery_worker-1  | - ** ---------- [config]
celery_worker-1  | - ** ---------- .> app:         nautobot:0x7285e713d550
celery_worker-1  | - ** ---------- .> transport:   redis://:**@redis:6379/0
celery_worker-1  | - ** ---------- .> results:     
celery_worker-1  | - *** --- * --- .> concurrency: 80 (prefork)
celery_worker-1  | -- ******* ---- .> task events: ON
celery_worker-1  | --- ***** ----- 
celery_worker-1  |  -------------- [queues]
celery_worker-1  |                 .> default          exchange=default(direct) key=default
celery_worker-1  |                 
celery_worker-1  | 
celery_beat-1    | 
celery_beat-1 exited with code 1
nautobot-1       |   Applying dcim.0003_initial_part_3... OK
nautobot-1       |   Applying virtualization.0001_initial... OK
....
nautobot-1       |   Applying extras.0011_fileattachment_fileproxy... OK
nautobot-1       |   Applying extras.0012_healthchecktestmodel... OK
nautobot-1       |   Applying extras.0013_default_fallback_value_computedfield... OK
nautobot-1       |   Applying extras.0014_auto_slug... OK
nautobot-1       |   Applying extras.0015_scheduled_job... OK
nautobot-1       |   Applying extras.0016_secret... OK
nautobot-1       |   Applying extras.0017_joblogentry... OK
nautobot-1       |   Applying extras.0018_joblog_data_migration... OK
nautobot-1       |   Applying extras.0019_joblogentry__meta_options__related_name... OK
nautobot-1       |   Applying extras.0020_customfield_changelog... OK
nautobot-1       |   Applying extras.0021_customfield_changelog_data... OK
nautobot-1       |   Applying extras.0022_objectchange_object_datav2... OK
nautobot-1       |   Applying extras.0023_job_model... OK
nautobot-1       |   Applying extras.0024_job_data_migration... OK
nautobot-1       |   Applying extras.0025_add_advanced_ui_boolean_to_customfield_conputedfield_and_relationship... OK
```

Once you see this output below the Nautobot containers will be ready to use:

```bash
nautobot-1       | ⏳ Running initial systems check...
nautobot-1       | 02:44:28.210 WARNING nautobot.core.api.routers routers.py                   get_api_root_view() :
nautobot-1       |   Something has changed an OrderedDefaultRouter's APIRootView attribute to a custom class. Please verify that class GoldenConfigRootView implements appropriate authentication controls.
nautobot-1       | 02:44:39.743 DEBUG   nautobot.core.utils.querysets querysets.py              maybe_select_related() :
nautobot-1       |   Applying .select_related(['backup_repository', 'intended_repository', 'jinja_repository', 'sot_agg_query', 'dynamic_group']) to GoldenConfigSetting QuerySet
nautobot-1       | 02:44:39.744 DEBUG   nautobot.core.utils.querysets querysets.py            maybe_prefetch_related() :
nautobot-1       |   Applying .prefetch_related(['tags']) to GoldenConfigSetting QuerySet
nautobot-1       | System check identified some issues:
nautobot-1       | 
nautobot-1       | WARNINGS:
nautobot-1       | ?: (drf_spectacular.W001) /usr/local/lib/python3.12/site-packages/nautobot_golden_config/api/serializers.py: Warning [ConfigToPushViewSet > ConfigToPushSerializer]: unable to resolve type hint for function "get_config". Consider using a type hint or @extend_schema_field. Defaulting to string.
nautobot-1       | ?: (drf_spectacular.W001) /usr/local/lib/python3.12/site-packages/nautobot_golden_config/filters.py: Warning [GoldenConfigSettingViewSet > GoldenConfigSettingFilterSet]: Unable to guess choice types from values, filter method's type hint or find "device_id" in model. Defaulting to string.
nautobot-1       | ?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. If your entire site is served only over SSL, you may want to consider setting a value and enabling HTTP Strict Transport Security. Be sure to read the documentation first; enabling HSTS carelessly can cause serious, irreversible problems.
nautobot-1       | ?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. Unless your site should be available over both SSL and non-SSL connections, you may want to either set this setting True or configure a load balancer or reverse-proxy server to redirect all connections to HTTPS.
nautobot-1       | ?: (security.W012) SESSION_COOKIE_SECURE is not set to True. Using a secure-only session cookie makes it more difficult for network traffic sniffers to hijack user sessions.
nautobot-1       | ?: (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' in your MIDDLEWARE, but you have not set CSRF_COOKIE_SECURE to True. Using a secure-only CSRF cookie makes it more difficult for network traffic sniffers to steal the CSRF token.
nautobot-1       | ?: (security.W018) You should not have DEBUG set to True in deployment.
nautobot-1       | 
nautobot-1       | System check identified 7 issues (0 silenced).
nautobot-1       | 02:45:01.470 WARNING nautobot.core.api.routers routers.py                   get_api_root_view() :
nautobot-1       |   Something has changed an OrderedDefaultRouter's APIRootView attribute to a custom class. Please verify that class GoldenConfigRootView implements appropriate authentication controls.
nautobot-1       | 02:45:20.377 WARNING nautobot.core.api.routers routers.py                   get_api_root_view() :
nautobot-1       |   Something has changed an OrderedDefaultRouter's APIRootView attribute to a custom class. Please verify that class GoldenConfigRootView implements appropriate authentication controls.
nautobot-1       | 02:45:22.920 INFO    django.utils.autoreload :
nautobot-1       |   Watching for file changes with StatReloader
nautobot-1       | Performing system checks...
nautobot-1       | 
nautobot-1       | System check identified no issues (0 silenced).
nautobot-1       | 02:45:25.045 INFO    nautobot             __init__.py                              setup() :
nautobot-1       |   Nautobot 2.4.2 initialized!
nautobot-1       | May 10, 2025 - 02:45:25
nautobot-1       | Django version 4.2.21, using settings 'nautobot_config'
nautobot-1       | Starting development server at http://0.0.0.0:8080/
nautobot-1       | Quit the server with CONTROL-C.
```
Lets get a username setup so we can login to the Nautobot GUI. From a new terminal window in your nautobot-docker-compose folder:

```bash
ubuntu@containerlabs:~/nautobot-docker-compose$ poetry shell
Spawning shell within /home/ubuntu/.cache/pypoetry/virtualenvs/nautobot-docker-compose-JnLSE0Mh-py3.12
ubuntu@containerlabs:~/nautobot-docker-compose$ . /home/ubuntu/.cache/pypoetry/virtualenvs/nautobot-docker-compose-JnLSE0Mh-py3.12/bin/activate
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/nautobot-docker-compose$ invoke createsuperuser
/home/ubuntu/nautobot-docker-compose/tasks.py:263: SyntaxWarning: invalid escape sequence '\$'
  export_cmd = 'exec db sh -c "mysqldump -u \${NAUTOBOT_DB_USER} –p \${NAUTOBOT_DB_PASSWORD} \${NAUTOBOT_DB_NAME} nautobot > /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:266: SyntaxWarning: invalid escape sequence '\$'
  export_cmd = 'exec db sh -c "pg_dump -h localhost -d \${NAUTOBOT_DB_NAME} -U \${NAUTOBOT_DB_USER} > /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:285: SyntaxWarning: invalid escape sequence '\$'
  import_cmd = 'exec db sh -c "mysql -u \${NAUTOBOT_DB_USER} –p \${NAUTOBOT_DB_PASSWORD} < /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
/home/ubuntu/nautobot-docker-compose/tasks.py:288: SyntaxWarning: invalid escape sequence '\$'
  import_cmd = 'exec db sh -c "psql -h localhost -U \${NAUTOBOT_DB_USER} < /tmp/nautobot.sql"'  # noqa: W605 pylint: disable=anomalous-backslash-in-string
Running docker compose command "ps --services --filter status=running"
Running docker compose command "exec nautobot nautobot-server createsuperuser --username admin"
02:49:27.405 WARNING nautobot.core.api.routers routers.py                   get_api_root_view() :
  Something has changed an OrderedDefaultRouter's APIRootView attribute to a custom class. Please verify that class GoldenConfigRootView implements appropriate authentication controls.
Email address: admin@admin.example
Password: 
Password (again): 
Superuser created successfully.
```

If you are using VSCODE you can click the ```http://0.0.0.0:8080/``` from the terminal or you can simply navigate to your container labs IP address ```http://<containerlab-ip>:8080/``` with the new superuser you created login to the Nautobot GUI and you should see this:
<img src="/assets/img/nautobot_workshop/nautobot-homepage.webp" alt="">

Navigate to the APPs - Installed Apps page to validate that the [Nornir](https://github.com/nautobot/nautobot-app-nornir), [BGP Models](https://github.com/nautobot/nautobot-app-bgp-models) and [Golden Config](https://github.com/nautobot/nautobot-app-golden-config) Apps from Network to Code have also been installed. To read about these apps head over to the Nautobot Github and check them out. These were included in the pyproject.toml in the root of the ```nautobot-docker-compose``` folder. If you ever want to install additional apps for Nautobot you can place them there and rebuild the image.

<img src="/assets/img/nautobot_workshop/nautobot-installed-app.webp" alt="">

## Conclusion
Now that our environment is setup and we will review the topology that will be represented by Nautobot and use that data to generate the Containerlab topology and device configurations. Join in for Part 2: Review the Network Topology.