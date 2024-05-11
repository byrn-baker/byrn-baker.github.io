---
title: Deploying K3s with Ansible - Part 5
date: 2024-03-24 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,ansible,rancher-ui,longhorn,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Adding longhorn with rancher-ui
While planning out what I wanted to use in my cluster I thought having Gitlab would be fun, but I needed a good way to supply persistent storage to install gitlab from its helm chart. Longhorn was an easy pick since I can just install it from the rancher UI and frankly this is all new anyway so lets see if we can put it together and see it working.

>  Longhorn addresses the need for reliable and scalable storage for stateful applications running in Kubernetes clusters, providing features such as replication, snapshots, backup, and restore in a cloud-native and Kubernetes-native manner.
{: .prompt-tip }

## Setting up NFS and ISCSI targets
The storage nodes can be all of your workers or just a couple, depends on what you want to do, I have an external iscsi storage system, so I thought why not use that for the nodes where I would expect storage workloads to be run. I added an additional host_var to my inventory for the iscsi target for each node. I then added a new set of tasks to the ```deploy-k3s-vms.yml``` so that after all the VMs were setup and before I run the ```sites.yml``` to build the cluster I would have the iscsi target mounted and ready to go for this installation of longhorn.

```yaml
{% raw %}
all:
  children:
    k3s_cluster:
      children:
        node:
          hosts:
            k3s11: 
              ansible_host: 192.168.30.48
              vmid: 2011
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s11.cc3fdd5a09f
            k3s12: 
              ansible_host: 192.168.30.49
              vmid: 2012
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s12.cc3fdd5a09f
            k3s13: 
              ansible_host: 192.168.30.50
              vmid: 2013
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s13.cc3fdd5a09f
{% endraw %}
```

Here are the additional tasks to mount an NFS share and an iscsi target to ubuntu. The set of tasks below are blocked and the when statement evaluates if you intend to have either installed before running the tasks. For the NFS share you would place the target in the group_vars, and the iscsi would be placed as a host_var in the inventory. The variables iscsi_target and iscsi_host would also be placed in the group_vars as well.
```yaml
{% raw %}
- name: Create and Mount NFS share to VMs
  hosts: node
  gather_facts: true

  tasks:
    - name: Install qemu-guest-agent, nfs-common, and open-iscsi
      ansible.builtin.apt:
        name: 
          - qemu-guest-agent
          - nfs-common
          - open-iscsi
        state: present
        update_cache: true
      become: true

    - block:     
      - name: Enable and start open-iscsi
        ansible.builtin.systemd:
          name: open-iscsi
          state: started
          enabled: yes
        become: true
      
      - block:
        - name: Ensure mount directory exists
          ansible.builtin.file:
            path: /mnt/longhorn/data
            state: directory
          become: true

        - name: Ensure NFS share is mounted
          ansible.posix.mount:
            path: /mnt/longhorn/data
            src: "{{ nfs_mount }}"
            fstype: nfs
            opts: defaults
            state: mounted
          become: true
      when: nfs_mount is defined
      
    - block:
      - name: Discover iscsi targets
        command: iscsiadm -m discovery -t st -p {{ iscsi_host }}
        become: true

      - name: Login to iscsi target
        command: iscsiadm -m node --targetname {{ hostvars[inventory_hostname]['iscsi_target'] }} --portal {{ iscsi_host }}:3260 --login
        become: true

      - name: Format the disk
        ansible.builtin.filesystem:
          fstype: ext4
          dev: /dev/sdb
        become: true
      
      - name: Create directory
        file:
          path: /mnt/iscsi
          state: directory
          mode: '0755'
        become: true

      - name: Mount the disk
        mount:
          path: /mnt/iscsi
          src: /dev/sdb
          fstype: ext4
          state: mounted
          opts: _netdev
        become: true

      - name: Add mount to fstab
        lineinfile:
          path: /etc/fstab
          line: '/dev/sdb /mnt/iscsi ext4 _netdev 0 0'
          state: present
        become: true
      when: hostvars[inventory_hostname]['iscsi_target'] is defined
{% endraw %}
```

## Installing Longhorn
Installing Longhorin the rancher is pretty straight forward. You navigate through the GUI to your local cluster, click on apps from the left side menu bar and select charts.
<img src="/assets/img/rancher-apps.webp" alt="">
In the filter bar just type longhorn. 
<img src="/assets/img/longhorn-app.webp" alt="">
I added an additional chart directly from longhorns helm, however by default the blue longhorn would be the only one that would show up at this point. Click on the longhorn and that will take you to an install screen. Click the install button on the top right
<img src="/assets/img/longhorn-install.webp" alt="">
select the customize helm option and use the default version and click next
<img src="/assets/img/longhorn-install-options.webp" alt="">
the only thing I made changes to in the helm values was to update the Longhorn Storage Class settings Default Storage Replica Count from 3 to 2. This is because Gitlab only deploys 2 containers and would always show an issue in Longhorns disk management because it was looking for 3 replicas and not 2.
<img src="/assets/img/longhorn-values-replica.webp" alt="">
click next and then install on the last screen. At this point if you click on Workloads and select Deployments you should see a new workload appear under the longhorn-system namespace, you can use kubectl. At some point I think installing longhorn will be something I will do with Ansible.

```bash
$ kubectl get deployments -n longhorn-system
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
csi-attacher               3/3     3            3           4d17h
csi-provisioner            3/3     3            3           4d17h
csi-resizer                3/3     3            3           4d17h
csi-snapshotter            3/3     3            3           4d17h
longhorn-driver-deployer   1/1     1            1           4d17h
longhorn-ui                2/2     2            2           4d17h
```