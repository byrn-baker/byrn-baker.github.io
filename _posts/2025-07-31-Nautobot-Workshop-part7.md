---
title: Nautobot Workshop Blog Series - Part 7 - Nautobot Golden Configuration - Configuration Backups
date: 2025-07-31 9:00:00
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
lab_vps_banner: true
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series

**Nautobot Workshop** is a hands-on blog series for building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting with a basic Ubuntu setup, each post walks through:

- Deploying Nautobot via `nautobot-docker-compose`
- Modeling topologies with Containerlab and vrnetlab routers
- Populating Nautobot with real device data using Ansible
- Generating configurations with Jinja2 templates
- Enforcing compliance with the Golden Config plugin
- Leveraging Nautobot’s GraphQL API for dynamic inventory

This series is perfect for network engineers aiming to combine source of truth, automation, and simulation in a streamlined workflow.

🚀 All project files are available in this [GitHub repo](https://github.com/byrn-baker/Nautobot-Workshop)


## Part 7 - Nautobot Golden Configuration - Configuration Backups
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/MqFuY3SriPE" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtube.com/shorts/MqFuY3SriPE)

Now that we have our containerlabs topology fully functions with a base configuration, we can walk through setting up the Nautobot Golden Configuration application and perform a configuration backup of each node.

You can read more about the [Nautobot Golden Configuration App here.](https://docs.nautobot.com/projects/golden-config/en/latest/)

Before configuring any of the Golden Configuration setting we need to create a Git token secret and github repo inside our Nautobot sandbox. Navigate over to the Secrets menu and select the blue plus sign creating a new secret. Provide a name and in the provider section use Environment Variable, and in the parameters sections under "Form" type in the variable being used for you github token.
<img src="/assets/img/nautobot_workshop/secrets.webp" alt="">


> When creating a token in github make sure the token can read and write to your repositories. The Nautobot Golden Configuration App will place files into this repository when performing backups of your router configs.
> The environment variables will need to be placed in your ```nautobot-docker-compose/environments/creds.env``` file.
> You will need the following:
> - GITHUB_TOKEN=!your token here!
> - NAPALM_USERNAME=admin
> - NAPALM_PASSWORD=admin
> - DEVICE_SECRET=admin
> The Napalm user and password will be used by the Golden Configuration application to log in to your routers.
{: .prompt-tip }

Next create a secrets group by using the blue plus sign and from the Access type drop down select HTTP(s), from the secrets type use "token", and select your github secret from the Secrets dropdown.
<img src="/assets/img/nautobot_workshop/secrets-group.webp" alt="">

Now click the Extensibility menu and then the Git Repositories blue plus sign under "DATA SOURCES" to add your github repository. 

Give a name and in the remote URL use the HTTP option from the github green code button under Local Clone. Use the branch where you would like to keep this data, and then select all of the "provides" you would like to sync between nautobot and this repository. 

> Create three repositories for the Jinja templates, intended configs, and backup configs, or you can fork mine [tempaltes](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates.git), [intended-configs](https://github.com/byrn-baker nautobot_workshop_golden_config_intended_configs), [backup-configs](https://github.com/byrn-baker/nautobot_workshop_golden_config_backup_configs). Select the appropriate provides for each one.
{: .prompt-tip }

<img src="/assets/img/nautobot_workshop/github_repo.webp" alt="">

> You can use a single repo for this, however seperate repos for each of the Gold Config provides is a little easier to manage in the long run.
{: .prompt-tip }

At the bottom click the create & sync button. If all goes well you should see a completed status on this job.
<img src="/assets/img/nautobot_workshop/git-repo-completed.webp" alt="">

We need to create a graphql that will be used to pull the data, the [Golden Configuration documentation provides one](https://docs.nautobot.com/projects/golden-config/en/latest/user/app_feature_sotagg/#performance), but we have our own from the work we did in Ansible, so we will just use that one because it works perfectly with our templates already. Under Extensibility click the blue plus sign on GraphQL Queries, give it a name and paste the query.

<img src="/assets/img/nautobot_workshop/graphql_query.webp" alt="">

```graphql
query ($device_id: ID!) {
    device(id: $device_id) {
      hostname: name
      config_context
      bgp_routing_instances {
      extra_attributes
      autonomous_system {
        asn
      }
      address_families {
        afi_safi
        extra_attributes
      }
      peer_groups {
        name
        source_interface {
          name
        }
        autonomous_system {
          asn
        }
        extra_attributes
        secret {
          name
        }
        address_families{
          import_policy
          export_policy
          extra_attributes
        }
        peergroup_template {
          autonomous_system {
            asn
          }
          extra_attributes
        }
        address_families {
          afi_safi
          import_policy
          export_policy
        }
      }
      endpoints {
        peer_group {
          name
        }
        source_ip {
          address
        }
        source_interface {
            name
          }
        description
        peer {
          description          
          source_ip {
            address
          }
          address_families {
            afi_safi
            import_policy
            export_policy
          }
          autonomous_system {
            asn
          }
          routing_instance {
            autonomous_system {
              asn
            }
          }
        }
      }
    }
      position
      serial
      role {
        name
      }
      primary_ip4 {
        id
        primary_ip4_for {
          id
          name
        }
      }
      tenant {
        name
      }
      tags {
        name
      }
      role {
        name
      }
      platform {
        name
        network_driver
        manufacturer {
          name
        }
        network_driver
        napalm_driver
      }
      location {
        name
        vlans {
          name
          vid
          vlan_group {
            name
          }
        }
        parent {
          name
          vlans {
          name
          vid
          vlan_group {
            name
          }
        }
        }
      }
      interfaces {
        name
        description
        mac_address
        enabled
        mgmt_only
        label
        lag {
          name
        }
        cf_ospf_network_type
        cf_ospf_area
        cf_mpls_enabled
        cf_vrrp_group_id
        cf_vrrp_ipv4_enabled
        cf_vrrp_ipv6_enabled
        cf_vrrp_disabled
        cf_vrrp_preempt
        cf_vrrp_priority_level
        cf_vrrp_advertisement_interval
        cf_vrrp_bfd_enabled
        cf_vrrp_mac_advertisement_interval
        cf_vrrp_peer_address
        cf_vrrp_session_name
        cf_vrrp_timer_interval
        cf_vrrp_tracked_object
        ip_addresses {
          address
          tags {
            id
          }
        }
        mode
        tagged_vlans {
          vid
        }
        untagged_vlan {
          vid
        }
        connected_interface {
          name
          device {
            name
          }
        }
        cf_mlag_interface
        tags {
          id
        }
      }
    }
  }
```

Now select the Golden Config Settings under the Golden Config menu, there should already be a settings called "default". We will use this for our example. Click on this and edit using the edit button on the top right. Under the Backup Configuration section from the backup repository drop down choose the repository we just created, and for the backup path we will use this in our form - ```{{obj.location.name|slugify}}/{{obj.name}}.cfg```. We can leave the Backup Test checked. Under the Templates Configuration section in the SOT AGG Query dropdown choose the graphql we just created above. Once done click update.

Now navigate over to the JOBS menu and select Jobs. We will need to enable all of the Nautobot Golden Configuration Jobs so that we can use them later and the Backup configs job now. Select each one by checking each check mark, and clicking edit at the bottom left of the page (edit selected). On the top choose YES in the attributes called Enabled and click apply at the bottom right.
<img src="/assets/img/nautobot_workshop/jobs.webp" alt="">
<img src="assets/img/nautobot_workshop/jobs-enabled.webp" alt="">

Now click the Backup Configurations job at the top of the list. From the platform section choose both the EOS and IOS platforms and click the Run Job Now button on the bottom right.
<img src="/assets/img/nautobot_workshop/backup-job.webp" alt="">

If we have done everything correctly we should see this job end with a status of completed, and in the logs you will see that each router was logged into and configs we retrieved and backed up. These backups will be synced to your repository under the ```backup-config``` folder.
<img src="/assets/img/nautobot_workshop/backup-job-completed.webp" alt="">

## Conclusion
In this post, we demonstrated how to integrate the Nautobot Golden Configuration application into our automated lab environment to perform configuration backups across network devices. By setting up secrets, linking a GitHub repository, creating a GraphQL query, and configuring the Golden Config settings, we established a reliable and repeatable workflow for capturing and storing device configurations. This ensures that our lab remains consistent and version-controlled, while also laying the foundation for future compliance checks and configuration drift detection. With backups now automatically pushed to Git, we’re one step closer to a fully operational, automated network lab built on Nautobot.