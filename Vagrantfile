# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64"

  config.ssh.insert_key = false

  config.vm.provision "ansible_local" do |ansible|
    ansible.verbose = "vv"
    ansible.install_mode = "pip"
    ansible.pip_install_cmd = "curl https://bootstrap.pypa.io/get-pip.py | sudo python3"
    ansible.playbook = "./ansible_scripts/provision/provision-null.yml"
  end

  config.vm.define "dev" do |dev|
    dev.vm.hostname = "dev"
    dev.vm.network "private_network", ip: "192.168.1.33"

    dev.vm.provider "virtualbox" do |v|
      v.memory = 1024
      v.cpus = 1
    end

    dev.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "./ansible_scripts/provision/provision-dev.yml"
    end
  end

  config.vm.define "gitlab" do |gitlab|
    gitlab.vm.hostname = "gitlab"
    gitlab.vm.network "private_network", ip: "192.168.1.34"

    gitlab.vm.provider "virtualbox" do |v|
      v.memory = 8704
      v.cpus = 2
    end

    gitlab.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "./ansible_scripts/provision/provision-gitlab.yml"
    end
  end

  config.vm.define "backend" do |backend|
    backend.vm.hostname = "backend"
    backend.vm.network "private_network", ip: "192.168.1.35"

    backend.vm.provider "virtualbox" do |v|
      v.memory = 1024
      v.cpus = 1
    end

    backend.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "./ansible_scripts/provision/provision-backend.yml"
    end
  end

  config.vm.define "frontend" do |frontend|
    frontend.vm.hostname = "frontend"
    frontend.vm.network "private_network", ip: "192.168.1.36"

    frontend.vm.provider "virtualbox" do |v|
      v.memory = 512
      v.cpus = 1
    end

    frontend.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "./ansible_scripts/provision/provision-frontend.yml"
    end
  end
end
