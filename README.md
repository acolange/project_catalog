# project_catalog
Udacity Fullstack Nanodegree Item Catalog Project

This is the project for the Udacity Product Catalog project.  To run this project you need to have [Python](https://www.python.org), [Vagrant](https://www.vagrantup.com), and [Gulp](https://www.gulpjs.com).

To run this project after cloning this repository, setting up vagrant, and installing gulp; you will need to access the directory containing the vagrantfile.

Once there run `vagrant up` to start your vagrant box.

After the vagrant box has started use `vagrant ssh` to access the vagrant box command line.  From there use `/vagrant/catalog` to get into the directory for the project.

If this is the first time you have run this project you will need to run the the database setup first using `python database_setup.py`.
